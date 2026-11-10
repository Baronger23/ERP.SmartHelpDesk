# Hướng dẫn Vận hành ERPNext Local qua Docker

Thư mục này chứa các script tiện ích để quản lý cụm container ERPNext v16 chạy trên Docker Desktop của bạn.

## 1. Thông số môi trường Local
- **URL**: [http://localhost:8080](http://localhost:8080)
- **Tài khoản quản trị**: `Administrator` / `admin`
- **Phiên bản**: Frappe Framework `v16.33.1`, ERPNext `v16.34.2`
- **Thư mục cấu hình Docker**: `e:\DUT.K1N4\HTTT\frappe_docker`

## 2. Các thao tác nhanh
- **Bật hệ thống**: Click đúp vào file [`start.bat`](start.bat) hoặc gõ:
  ```bash
  docker compose -f ../../frappe_docker/pwd.yml start
  ```
- **Tạm dừng hệ thống** (để tiết kiệm RAM khi không dùng): Click đúp vào file [`stop.bat`](stop.bat) hoặc gõ:
  ```bash
  docker compose -f ../../frappe_docker/pwd.yml stop
  ```
- **Kiểm tra trạng thái container**:
  ```bash
  docker compose -f ../../frappe_docker/pwd.yml ps
  ```

## 3. Cấu hình kết nối API
Để các script trong dự án tự động kết nối với local instance này, đảm bảo file [`.env`](../.env) ở thư mục gốc có các thông số:
```env
FRAPPE_BASE_URL=http://localhost:8080
FRAPPE_API_KEY=f76b087b4d0fd45
FRAPPE_API_SECRET=e00918ed98d7fd8
```
*(Nếu muốn chuyển lại lên Frappe Cloud, chỉ cần sao chép nội dung từ `.env.cloud` sang `.env`).*

## 4. Cài/cập nhật app SmartHelpDesk trong Docker

Từ 2026-11-10 app đã về dạng Frappe chuẩn (DocType khai bằng JSON trong
`apps/smart_helpdesk`), nên trong Docker cũng cài bằng cơ chế chuẩn:

1. Bật stack (kèm overlay gắn thư mục app của repo vào container):
   đặt biến môi trường `SHD_APP_PATH` trỏ tới `apps/smart_helpdesk` của repo,
   rồi `docker compose -f ../../frappe_docker/pwd.yml -f compose.business.yml up -d`
   (hoặc `start` nếu container đã tạo).
2. Đảm bảo bench trong container có dòng `smart_helpdesk` trong `sites/apps.txt`
   — thiếu dòng này `bench install-app` sẽ báo "App smart_helpdesk not in apps.txt".
3. Chạy installer: `python docker/install_business_app.py`
   (sao lưu DB + files trước, rồi `bench --site frontend install-app smart_helpdesk`
   và `migrate` trong container, kèm vá cấu hình realtime).

Đã kiểm chứng 2026-11-10: tạo site dùng một lần ngay trong container bằng app
chuẩn mới cho đủ 28 bảng `tabSHD ...`, sau đó xóa site.
