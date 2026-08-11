# Gợi ý làm bài

## Khi log thiếu correlation ID

Theo dõi một request từ middleware đến response. Kiểm tra context có được xóa trước request mới, gán vào logger và trả lại trong response header hay chưa.

## Khi log thiếu metadata

Xác định metadata nào thuộc toàn request và metadata nào chỉ xuất hiện sau khi agent chạy xong. Bind context trước dòng `request_received` để các log sau dùng chung context.

## Khi còn PII trong log

Kiểm tra thứ tự processor: dữ liệu phải được scrub trước khi JSON được render và ghi xuống file. Thử với email, số điện thoại và số thẻ mẫu.

## Khi metrics báo xấu nhưng chưa biết nguyên nhân

1. Dùng metrics xác định khoảng thời gian và loại triệu chứng.
2. Mở một trace bất thường trong khoảng đó.https://github.com/buitunglam308work-stack/Day13-K4-Observability
3. So sánh thời gian các span.
4. Tìm log có cùng correlation ID.
5. Chỉ kết luận khi evidence khớp ở cả ba lớp.

## Khi dashboard khó đọc

Mỗi panel cần tên, đơn vị, khoảng thời gian và threshold. Ưu tiên 6 panel chính thay vì thêm nhiều biểu đồ không phục vụ quyết định.

Chạy `python scripts/validate_dashboard.py` trước. Nếu validator qua nhưng dashboard vẫn sai, đối chiếu từng event/field với bảng trong [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md), đặc biệt `response_sent.latency_ms` và `response_sent.quality_score`.

## Khi prompt luôn hiện `local-v1`

1. Kiểm tra `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` và `LANGFUSE_HOST`.
2. Kiểm tra prompt name/label trong `.env` có tồn tại trên đúng project không.
3. Khởi động lại API sau khi đổi `.env`.
4. Mở trace metadata: `prompt_source=local` nghĩa là chưa bật Langfuse; `local-fallback` nghĩa là đã bật nhưng fetch prompt lỗi.

Không sửa code để ghi giả version. Làm theo [PROMPT_VERSIONING.md](PROMPT_VERSIONING.md) và lấy trace thật làm evidence.
