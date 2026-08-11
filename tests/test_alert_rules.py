from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_alerts_align_with_slo_thresholds_and_runbooks() -> None:
    dashboard = yaml.safe_load(
        (REPO_ROOT / "config/dashboard.yaml").read_text(encoding="utf-8")
    )["dashboard"]
    alerts = yaml.safe_load(
        (REPO_ROOT / "config/alert_rules.yaml").read_text(encoding="utf-8")
    )["alerts"]
    runbooks = (REPO_ROOT / "docs/alerts.md").read_text(encoding="utf-8")
    thresholds = {
        panel["id"]: panel["threshold"]["value"] for panel in dashboard["panels"]
    }

    assert len(alerts) == 3
    assert [alert["name"] for alert in alerts] == [
        "HighChatLatency",
        "ElevatedChatErrorRate",
        "DailyCostBudgetExceeded",
    ]
    assert str(thresholds["latency"]) in alerts[0]["condition"]
    assert str(thresholds["errors"]) in alerts[1]["condition"]
    assert str(thresholds["cost"]) in alerts[2]["condition"]

    for index, alert in enumerate(alerts, start=1):
        assert alert["type"] == "symptom-based"
        assert alert["severity"] in {"warning", "critical"}
        assert alert["owner"] == "Bùi Tùng Lâm"
        assert alert["runbook"] == f"docs/alerts.md#alert-{index}"
        assert f"## Alert {index}" in runbooks
        assert alert["name"] in runbooks
