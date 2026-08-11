# Prompt versioning cơ bản

Mục tiêu của phần này là biết một request đã dùng prompt nào và có thể rollback an toàn. Đây không phải bài tối ưu prompt hoặc A/B testing.

## Prompt contract

Tạo text prompt tên `day13-chat` trên Langfuse. Prompt phải giữ ba biến:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

App lấy prompt theo hai biến môi trường:

```dotenv
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

Nếu Langfuse không khả dụng, app dùng template local và trace metadata ghi `prompt_source=local` hoặc `local-fallback` thay vì giả vờ đã lấy được prompt managed.

## Việc cần làm

1. Tạo version 1, gắn labels `baseline` và `production`.
2. Tạo version 2 với một thay đổi nhỏ về format hoặc độ dài câu trả lời, gắn label `candidate`.
3. Chạy cùng một input với `LANGFUSE_PROMPT_LABEL=baseline` và `candidate`.
4. Mở hai trace, kiểm tra `prompt_name`, `prompt_label`, `prompt_version` và prompt link.
5. Chuyển label `production` sang version 2, chạy lại một request.
6. Rollback `production` về version 1 và lưu ảnh evidence.

Không chấm prompt nào “hay hơn”. Điểm nằm ở khả năng truy xuất version, đổi label và rollback có bằng chứng.

## Evidence

- Một ảnh danh sách hai prompt version.
- Hai trace ID chứng minh hai version/label khác nhau.
- Một ảnh trước/sau khi đổi label hoặc rollback `production`.
- Ghi các ID và đường dẫn ảnh vào `submission/REPORT.md`.

## Phiên bản của nhóm

Nhóm đã tạo prompt text `day13-chat` với hai phiên bản giữ nguyên ba biến
`feature`, `docs`, `message`:

- v1 (`baseline`, `production`): trợ lý observability ngắn gọn, chỉ dùng tài
  liệu được cung cấp và không bịa thông tin còn thiếu.
- v2 (`candidate`): format điều tra incident theo tối đa ba bullet `finding`,
  `evidence`, `next action`, đồng thời phải nói rõ khi evidence chưa đủ.

Cùng câu hỏi “How do metrics, traces, and logs identify a latency incident?”
đã được chạy với hai label:

- `baseline` / v1: trace `c957936411f4ae5ee92681e238323ac5`.
- `candidate` / v2: trace `8973329bd9d9ff5a3990f0ef9d75b701`.

Kiểm tra rollback đã thực hiện theo thứ tự: chuyển `production` sang v2 (trace
`630a47ad84eef68d6d542db8225e9ac0`), sau đó chuyển `production` về v1 (trace
`ccb4fc7992177ace07514e9346659dbd`). Trạng thái cuối cùng là
`production = v1`, `candidate = v2`, `baseline = v1`.
