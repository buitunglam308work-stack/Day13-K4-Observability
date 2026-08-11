from __future__ import annotations

import json
from types import SimpleNamespace

from dashboard import server as dashboard_server


class FakeBackendResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self.headers = {"Content-Type": "application/json"}
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_dashboard_proxy_forwards_chat_payload_and_request_id(monkeypatch) -> None:
    captured = SimpleNamespace(request=None, timeout=None)

    def fake_urlopen(request, timeout):
        captured.request = request
        captured.timeout = timeout
        return FakeBackendResponse(
            {
                "answer": "Refund approved",
                "correlation_id": "req-chat-01",
                "latency_ms": 250,
                "tokens_in": 12,
                "tokens_out": 8,
                "cost_usd": 0.00001,
                "quality_score": 0.8,
            }
        )

    monkeypatch.setattr(dashboard_server, "urlopen", fake_urlopen)
    payload = {
        "user_id": "dashboard-user",
        "session_id": "dashboard-session",
        "feature": "qa",
        "message": "Refund thế nào?",
    }

    status, content_type, body = dashboard_server.proxy_backend_request(
        "http://127.0.0.1:8000",
        "/chat",
        method="POST",
        payload=payload,
        request_id="req-chat-01",
    )

    assert status == 200
    assert content_type == "application/json"
    assert json.loads(body) == {
        "answer": "Refund approved",
        "correlation_id": "req-chat-01",
        "latency_ms": 250,
        "tokens_in": 12,
        "tokens_out": 8,
        "cost_usd": 0.00001,
        "quality_score": 0.8,
    }
    assert captured.request.full_url == "http://127.0.0.1:8000/chat"
    assert captured.request.get_method() == "POST"
    assert json.loads(captured.request.data) == payload
    assert captured.request.get_header("X-request-id") == "req-chat-01"
    assert captured.timeout == 60
