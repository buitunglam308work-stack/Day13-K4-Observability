from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_records(path: Path, *, now: datetime, window_minutes: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    window_start = now - timedelta(minutes=window_minutes)
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = _parse_timestamp(record.get("ts"))
        if timestamp is not None and window_start <= timestamp <= now:
            records.append(record)
    return records


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile_value / 100) * len(ordered)))
    return float(ordered[rank - 1])


def _numeric(records: list[dict[str, Any]], field: str) -> list[float]:
    return [
        float(record[field])
        for record in records
        if isinstance(record.get(field), (int, float))
    ]


def _panel_values(panel_id: str, records: list[dict[str, Any]], window_minutes: int) -> dict[str, Any]:
    received = [record for record in records if record.get("event") == "request_received"]
    failed = [record for record in records if record.get("event") == "request_failed"]
    responses = [record for record in records if record.get("event") == "response_sent"]

    if panel_id == "latency":
        values = _numeric(responses, "latency_ms")
        return {
            "primary": percentile(values, 95),
            "primary_aggregation": "p95",
            "breakdown": {
                "p50": percentile(values, 50),
                "p95": percentile(values, 95),
                "p99": percentile(values, 99),
            },
        }
    if panel_id == "traffic":
        timestamps = [
            timestamp
            for record in received
            if (timestamp := _parse_timestamp(record.get("ts"))) is not None
        ]
        observed_minutes = 1
        if len(timestamps) > 1:
            observed_seconds = (max(timestamps) - min(timestamps)).total_seconds()
            observed_minutes = max(
                1, min(window_minutes, math.ceil(observed_seconds / 60))
            )
        return {
            "primary": round(len(received) / observed_minutes, 3),
            "primary_aggregation": "rate_per_minute",
            "breakdown": {
                "count": len(received),
                "observed_minutes": observed_minutes,
            },
        }
    if panel_id == "errors":
        error_rate = (len(failed) / len(received) * 100) if received else 0.0
        breakdown: dict[str, int] = {}
        for record in failed:
            error_type = str(record.get("error_type") or "UnknownError")
            breakdown[error_type] = breakdown.get(error_type, 0) + 1
        return {
            "primary": round(error_rate, 3),
            "primary_aggregation": "error_rate_pct",
            "breakdown": breakdown or {"request_failed": 0},
        }
    if panel_id == "cost":
        costs = _numeric(responses, "cost_usd")
        return {
            "primary": round(sum(costs), 6),
            "primary_aggregation": "total",
            "breakdown": {"responses": len(costs)},
        }
    if panel_id == "tokens":
        tokens_in = sum(_numeric(responses, "tokens_in"))
        tokens_out = sum(_numeric(responses, "tokens_out"))
        return {
            "primary": tokens_in + tokens_out,
            "primary_aggregation": "sum_by_field",
            "breakdown": {"tokens_in": tokens_in, "tokens_out": tokens_out},
        }
    if panel_id == "quality":
        quality_scores = _numeric(responses, "quality_score")
        quality_mean = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        return {
            "primary": round(quality_mean, 3),
            "primary_aggregation": "mean",
            "breakdown": {"responses": len(quality_scores)},
        }
    raise ValueError(f"Unsupported dashboard panel: {panel_id}")


def build_dashboard(config_path: Path, log_path: Path, *, now: datetime | None = None) -> dict[str, Any]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    dashboard = payload["dashboard"]
    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    window_minutes = int(dashboard["time_range_minutes"])
    records = load_records(log_path, now=generated_at, window_minutes=window_minutes)

    panels = []
    for panel in dashboard["panels"]:
        values = _panel_values(panel["id"], records, window_minutes)
        threshold = panel["threshold"]
        primary = values["primary"]
        target = threshold["value"]
        healthy = primary <= target if threshold["operator"] == "lte" else primary >= target
        panels.append(
            {
                "id": panel["id"],
                "title": panel["title"],
                "unit": panel["unit"],
                "threshold": threshold,
                "healthy": healthy,
                **values,
            }
        )

    return {
        "title": dashboard["title"],
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "time_range_minutes": window_minutes,
        "refresh_seconds": dashboard["refresh_seconds"],
        "record_count": len(records),
        "panels": panels,
    }


def make_handler(config_path: Path, log_path: Path):
    class DashboardHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

        def do_GET(self) -> None:
            if self.path.split("?", 1)[0] != "/api/dashboard":
                return super().do_GET()

            try:
                payload = build_dashboard(config_path, log_path)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
            except Exception as exc:
                body = json.dumps(
                    {"error": type(exc).__name__, "detail": str(exc)}, ensure_ascii=False
                ).encode("utf-8")
                self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return DashboardHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Day 13 runtime dashboard")
    parser.add_argument(
        "--host", default=os.getenv("DASHBOARD_HOST", "127.0.0.1")
    )
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("DASHBOARD_PORT", "8080"))
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.getenv("DASHBOARD_CONFIG_PATH", REPO_ROOT / "config/dashboard.yaml")),
    )
    parser.add_argument(
        "--logs",
        type=Path,
        default=Path(os.getenv("DASHBOARD_LOG_PATH", REPO_ROOT / "data/logs.jsonl")),
    )
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), make_handler(args.config, args.logs))
    print(f"Dashboard: http://{args.host}:{args.port}")
    print(f"Config: {args.config}")
    print(f"Logs: {args.logs}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
