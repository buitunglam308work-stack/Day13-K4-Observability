# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: K4 Observability Team
- Repository URL: https://github.com/buitunglam308work-stack/Day13-K4-Observability
- Commit SHA cuối: lấy bằng `git rev-parse HEAD` tại thời điểm nộp.
- Thành viên và vai trò:
  - Bùi Tùng Lâm — Dashboard, SLO & Alert.
  - Chu Tâm Vũ (`ctz13104@gmail.com`) — Logging & PII.
  - Trần Anh Tú (`tutran0401@gmail.com`) — Tracing & Prompt Version.
  - Nguyễn Đức Anh Tuấn (`nguyenducanhtuan22092004@gmail.com`) — Incident, Report & Demo.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 trên 112 records tại lần chạy cuối;
  xem `submission/evidence/validate_logs.txt`.
- Tổng số traces: 37 trace được xác nhận qua Langfuse API ngày 2026-08-11,
  gồm trace load test, prompt versioning và challenge. Cần chụp màn hình danh
  sách trace trên Langfuse trước khi nộp.
- Số PII leak còn lại: 0 theo validator.
- Link/đường dẫn dashboard: `dashboard/`; ảnh baseline tại
  `submission/evidence/dashboard-runtime.png`, ảnh sau challenge tại
  `submission/evidence/dashboard-after-challenge.png`.

## 3. Logging và tracing

- Evidence correlation ID: `req-feedface` liên kết tới trace
  `2431a25be1b0ce83362964beb02fde58`; official challenge dùng
  `req-f4342824` và trace `2e12db77f287f04be3a61418a4e558e7`.
- Evidence PII redaction: log baseline thay email, số điện thoại và số thẻ bằng
  `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`; validator
  không phát hiện chuỗi PII thô.
- Evidence trace waterfall: `submission/evidence/challenge-run.txt`; cần bổ
  sung ảnh waterfall trực tiếp từ Langfuse UI trước khi nộp.
- Giải thích một span đáng chú ý: trong official trace
  `2e12db77f287f04be3a61418a4e558e7`, `rag-retrieval` mất 2500 ms trong khi
  `fake-llm` chỉ mất 150 ms. Retrieval là span chi phối latency.

## 4. Prompt versioning

- Prompt name: `day13-chat`.
- Version/label baseline: v1 / `baseline` và trạng thái cuối `production`.
- Version/label candidate: v2 / `candidate`.
- Trace ID của mỗi version: baseline
  `c957936411f4ae5ee92681e238323ac5`; candidate
  `8973329bd9d9ff5a3990f0ef9d75b701`.
- Bằng chứng đổi label hoặc rollback: production-v2 trace
  `630a47ad84eef68d6d542db8225e9ac0`; sau rollback về v1 trace
  `ccb4fc7992177ace07514e9346659dbd`. Cần bổ sung ảnh thao tác label trên UI.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel`.
- Evidence dashboard: `submission/evidence/dashboard-runtime.png` (baseline)
  và `submission/evidence/dashboard-after-challenge.png` (P95 3835 ms, breach);
  cả hai đọc trực tiếp `data/logs.jsonl` và lấy time range/unit/threshold từ
  contract YAML.
- SLO đã chọn và lý do: latency P95 ≤ 3000 ms và error rate ≤ 2% bảo vệ trải
  nghiệm người dùng; daily cost ≤ 2.5 USD bảo vệ ngân sách; quality trung bình
  ≥ 0.75 phát hiện suy giảm chất lượng.
- Alert rules và runbook: `HighChatLatency`, `ElevatedChatErrorRate`,
  `DailyCostBudgetExceeded` trong `config/alert_rules.yaml`; runbook tương ứng
  tại `docs/alerts.md#alert-1` đến `#alert-3`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`, cohort K4.
- Triệu chứng từ metrics: 5/5 request có latency vượt 2000 ms; P50 2651 ms,
  P95/P99 3835 ms. Practice trước đó tăng P95 từ 1432 ms lên 2650 ms.
- Trace ID liên quan: `2e12db77f287f04be3a61418a4e558e7`.
- Log line/correlation ID liên quan: event `response_sent`, correlation ID
  `req-f4342824`, latency 3835 ms, cùng trace ID ở trên.
- Root cause: incident `rag_slow` làm span `rag-retrieval` mất 2500 ms; span
  `fake-llm` chỉ 150 ms nên LLM không phải bottleneck.
- Fix action: tắt `rag_slow` sau khi thu evidence; trong hệ thống thật cần
  timeout/circuit breaker và fallback cho retrieval chậm.
- Preventive measure: alert theo P95 duy trì 5 phút, theo dõi riêng span
  retrieval, đặt timeout budget, cache kết quả phù hợp và chạy canary/load test
  trước release.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Bùi Tùng Lâm | Dashboard runtime, SLO, alert rules và runbook | 3 commit dưới identity `buitunglam308.work@gmail.com` | Chuyển SLI/SLO thành panel và alert theo triệu chứng |
| Chu Tâm Vũ | Correlation ID, log enrichment và PII redaction | 3 commit dưới identity `ctz13104@gmail.com` | Context propagation và scrub trước file sink |
| Trần Anh Tú | Managed prompt v1/v2, metadata trace và rollback | 3 commit dưới identity `tutran0401@gmail.com` | Liên kết prompt label/version với trace |
| Nguyễn Đức Anh Tuấn | Nested spans, practice/challenge investigation và report | 3 commit dưới identity `nguyenducanhtuan22092004@gmail.com` | Điều tra Metrics → Trace → Log bằng evidence |
