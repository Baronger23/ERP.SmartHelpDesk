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
