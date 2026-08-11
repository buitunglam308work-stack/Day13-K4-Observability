from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app import logging_config
from app.main import agent, app, health


@pytest.fixture(autouse=True)
def run_chat_without_external_trace_export(monkeypatch) -> None:
    run_without_observe = type(agent).run.__wrapped__
    monkeypatch.setattr(
        agent,
        "run",
        lambda **kwargs: run_without_observe(agent, **kwargs),
    )


def post_chat(payload: dict, headers: dict[str, str] | None = None) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.post("/chat", json=payload, headers=headers)

    return asyncio.run(send())


def test_health_exposes_active_llm_and_tracing_mode() -> None:
    payload = asyncio.run(health())

    assert payload["llm_provider"] == agent.provider
    assert payload["model"] == agent.model
    assert isinstance(payload["tracing_enabled"], bool)


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    response = post_chat(
        {
            "user_id": "student-01",
            "session_id": "session-01",
            "feature": "qa",
            "message": "Explain observability",
        }
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]


def test_chat_propagates_request_id_and_enriches_redacted_logs(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    response = post_chat(
        {
            "user_id": "student-02",
            "session_id": "session-02",
            "feature": "qa",
            "message": "Liên hệ student@vinuni.edu.vn, hộ chiếu C1234567",
        },
        headers={"x-request-id": "req-a1b2c3d4"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-a1b2c3d4"
    assert float(response.headers["x-response-time-ms"]) >= 0
    assert response.json()["correlation_id"] == "req-a1b2c3d4"

    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    api_events = [event for event in events if event.get("service") == "api"]
    assert api_events
    for event in api_events:
        assert event["correlation_id"] == "req-a1b2c3d4"
        assert event["user_id_hash"] != "student-02"
        assert event["session_id"] == "session-02"
        assert event["feature"] == "qa"
        assert event["model"] == agent.model
        assert event["env"]
        assert "student@vinuni.edu.vn" not in json.dumps(event, ensure_ascii=False)
        assert "C1234567" not in json.dumps(event, ensure_ascii=False)
