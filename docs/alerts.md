# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `HighChatLatency`
- Severity: `warning`
- SLI/SLO liên quan: `latency_p95_ms`, mục tiêu P95 không vượt quá 3000 ms.
- Điều kiện và thời gian duy trì: P95 latency lớn hơn 3000 ms liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: câu trả lời chat chậm, tăng nguy cơ timeout và người dùng gửi lại yêu cầu.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận time range và so sánh P50/P95/P99 để loại trừ một outlier đơn lẻ.
  2. Mở trace chậm trong cùng cửa sổ thời gian, tìm span chiếm phần lớn latency.
  3. Tra log bằng correlation ID của trace và kiểm tra trạng thái incident/dependency.
- Mitigation tạm thời: giảm concurrency hoặc lưu lượng vào service, tắt incident practice nếu đang bật, rồi kiểm tra lại P95 trong một cửa sổ 5 phút mới.
- Owner/người liên hệ: Bùi Tùng Lâm — Dashboard, SLO & Alert.

## Alert 2

- Tên: `ElevatedChatErrorRate`
- Severity: `critical`
- SLI/SLO liên quan: `error_rate_pct`, mục tiêu không vượt quá 2%.
- Điều kiện và thời gian duy trì: tỷ lệ `request_failed` trên `request_received` lớn hơn 2% liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: một phần yêu cầu chat trả lỗi thay vì câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra breakdown theo `error_type` để xác định nhóm lỗi đang tăng.
  2. Mở một trace lỗi đại diện và xác định span đầu tiên có trạng thái lỗi.
  3. Dùng correlation ID để đối chiếu `request_failed` và payload đã redact trong log.
- Mitigation tạm thời: cô lập tính năng hoặc dependency gây lỗi, rollback thay đổi gần nhất nếu có tương quan thời gian, và xác nhận error rate phục hồi dưới 2%.
- Owner/người liên hệ: Bùi Tùng Lâm — Dashboard, SLO & Alert.

## Alert 3

- Tên: `DailyCostBudgetExceeded`
- Severity: `warning`
- SLI/SLO liên quan: `daily_cost_usd`, ngân sách tối đa 2.5 USD/ngày.
- Điều kiện và thời gian duy trì: tổng `cost_usd` trong ngày lớn hơn 2.5 USD.
- Ảnh hưởng tới người dùng: chưa nhất thiết có lỗi tức thời, nhưng service có nguy cơ hết ngân sách hoặc bị giới hạn trước cuối ngày.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận tổng cost theo ngày và thời điểm cost bắt đầu tăng nhanh.
  2. So sánh traffic, token input/output và cost theo feature/model trong cùng cửa sổ.
  3. Mở trace có chi phí cao để kiểm tra prompt, token usage và incident `cost_spike`.
- Mitigation tạm thời: tắt incident practice nếu đang bật, giới hạn traffic không thiết yếu và chuyển về prompt/model đã được duyệt có mức token bình thường.
- Owner/người liên hệ: Bùi Tùng Lâm — Dashboard, SLO & Alert.
