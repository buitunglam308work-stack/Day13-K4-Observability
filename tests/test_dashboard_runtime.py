from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from dashboard.server import build_dashboard


def test_runtime_dashboard_aggregates_logs_using_contract(tmp_path: Path) -> None:
    now = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)
    records = [
        {"ts": "2026-08-11T07:59:00Z", "event": "request_received"},
        {"ts": "2026-08-11T07:59:01Z", "event": "request_received"},
        {
            "ts": "2026-08-11T07:59:02Z",
            "event": "response_sent",
            "latency_ms": 1200,
            "cost_usd": 0.25,
            "tokens_in": 100,
            "tokens_out": 200,
            "quality_score": 0.9,
        },
        {
            "ts": "2026-08-11T07:59:03Z",
            "event": "response_sent",
            "latency_ms": 3200,
            "cost_usd": 0.5,
            "tokens_in": 150,
            "tokens_out": 250,
            "quality_score": 0.8,
        },
        {
            "ts": "2026-08-11T07:59:04Z",
            "event": "request_failed",
            "error_type": "TimeoutError",
        },
        {"ts": "2026-08-11T05:00:00Z", "event": "request_received"},
    ]
    log_path = tmp_path / "logs.jsonl"
    log_path.write_text(
        "\n".join(json.dumps(record) for record in records), encoding="utf-8"
    )

    result = build_dashboard(
        Path("config/dashboard.yaml"), log_path, now=now
    )
    panels = {panel["id"]: panel for panel in result["panels"]}

    assert result["record_count"] == 5
    assert result["time_range_minutes"] == 60
    assert panels["latency"]["breakdown"] == {
        "p50": 1200.0,
        "p95": 3200.0,
        "p99": 3200.0,
    }
    assert panels["latency"]["healthy"] is False
    assert panels["traffic"]["primary"] == 2.0
    assert panels["traffic"]["breakdown"] == {
        "count": 2,
        "observed_minutes": 1,
    }
    assert panels["errors"]["primary"] == 50.0
    assert panels["errors"]["breakdown"] == {"TimeoutError": 1}
    assert panels["cost"]["primary"] == 0.75
    assert panels["tokens"]["breakdown"] == {
        "tokens_in": 250.0,
        "tokens_out": 450.0,
    }
    assert panels["quality"]["primary"] == 0.85
