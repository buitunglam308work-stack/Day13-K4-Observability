# Runtime dashboard

Dashboard này đọc trực tiếp `data/logs.jsonl` và contract
`config/dashboard.yaml`. Time range, refresh interval, unit và threshold không
được lặp lại trong frontend.

Từ thư mục gốc của repo, chạy:

```bash
.venv/bin/python dashboard/server.py
```

Sau đó mở <http://127.0.0.1:8080>. Trang này có giao diện chat proxy tới backend
FastAPI mặc định tại <http://127.0.0.1:8000>; mỗi tin nhắn tạo cùng log và trace
dùng cho dashboard. Có thể đổi địa chỉ, cổng và nguồn dữ liệu
bằng biến môi trường `DASHBOARD_HOST`, `DASHBOARD_PORT`,
`DASHBOARD_CONFIG_PATH`, `DASHBOARD_LOG_PATH`, hoặc các option tương ứng:

```bash
.venv/bin/python dashboard/server.py --host 0.0.0.0 --port 8080 \
  --config config/dashboard.yaml --logs data/logs.jsonl
```

Đổi backend bằng `DASHBOARD_API_BASE_URL` hoặc `--api-base-url`. Giao diện không
đọc hay lưu `OPENAI_API_KEY`; key chỉ được backend đọc từ môi trường.

Để tạo dữ liệu baseline, khởi động API rồi chạy
`python scripts/load_test.py --concurrency 5`. Dashboard tự đọc lại log theo
chu kỳ `refresh_seconds` trong contract.
