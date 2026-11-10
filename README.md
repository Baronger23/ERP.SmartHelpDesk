# Smart HelpDesk & Maintenance

Hệ thống dịch vụ bảo trì công nghiệp B2B trên ERPNext/Frappe. Custom app `apps/smart_helpdesk` hiện thực lõi nghiệp vụ theo bộ thiết kế v3. Agent Harness và tích hợp AI được hoãn; catalog tri thức kỹ thuật dùng độc lập.

## Vận hành local (bench — đường chính)

Môi trường phát triển chuẩn là **bench native trong WSL2/Ubuntu** (trên Windows)
hoặc Linux. Frappe v16 yêu cầu **Python 3.14** và **Node ≥ 24**; cần thêm MariaDB
(đã cấu hình utf8mb4 cho Frappe), Redis, yarn và wkhtmltopdf. Các phiên bản được
ghim đúng như bản đang vận hành: Frappe `v16.33.1`, ERPNext `v16.34.2`.

```bash
# 1. Tạo bench và lấy ERPNext
bench init --frappe-branch v16.33.1 --python python3.14 frappe-bench
cd frappe-bench
bench get-app --branch v16.34.2 erpnext

# 2. Tạo site và cài ERPNext
bench new-site shd.localhost --mariadb-root-password <root-password> --admin-password admin
bench --site shd.localhost install-app erpnext

# 3. Đưa app này vào bench (repo đã clone sẵn ở một thư mục khác)
cp -r /duong/dan/toi/repo/apps/smart_helpdesk apps/smart_helpdesk
./env/bin/pip install -e apps/smart_helpdesk
printf 'frappe\nerpnext\nsmart_helpdesk\n' > sites/apps.txt   # hoặc thêm dòng smart_helpdesk vào apps.txt sẵn có
bench --site shd.localhost install-app smart_helpdesk
bench --site shd.localhost migrate

# 4. Chạy
bench start
```

Mở [workspace Smart Helpdesk](http://shd.localhost:8000/desk/smart-helpdesk),
đăng nhập `Administrator` / `admin`, dùng **Tạo hồ sơ** và **Thao tác nghiệp vụ**.
Cài đặt xong, bench có đủ 28 DocType SHD, workspace Smart Helpdesk và 8 vai trò AIS.

[Hướng dẫn triển khai và vận hành](docs/implementation/business_modules.md) mô tả cấu hình scope/authority, policy SLA, chuỗi nghiệp vụ, API, giới hạn và phần chưa triển khai. Cần cấu hình khách/site/máy, hợp đồng, người duyệt và quyền trước vận hành; dữ liệu demo không tự thành chính sách đã duyệt.

### Môi trường Docker (phụ)

Docker chỉ còn là môi trường phụ để demo/kiểm thử nhanh: khởi động stack
`frappe_docker` rồi cài app chuẩn bằng `docker/install_business_app.py`
(script sao lưu DB, chạy `bench install-app smart_helpdesk` + migrate trong
container). Lưu ý: app được gắn vào container qua `docker/compose.business.yml`
và phải có tên trong `sites/apps.txt` của bench trong container thì
`install-app` mới nhận. Chi tiết: [docker/README.md](docker/README.md).

## Module nghiệp vụ

M01 khách hàng/hợp đồng · M02 tiếp nhận/SLA · M03 điều phối/tác nghiệp · M04 thiết bị/PM · M05 kho/reservation · M06 mua hàng · M07 chi phí/hóa đơn · M08 báo cáo/KPI · M09 catalog tri thức · M10 quyền/audit.

Request, incident, work order và visit có dữ liệu riêng. Reservation kiểm tra đồng thời trên Bin native. Approval gắn nội dung/version/expiry, mua/kho/hóa đơn dùng chứng từ ERPNext native; command và journal có transaction/idempotency. Tài liệu triển khai phân biệt thiết kế mục tiêu với mức hiện thực.

## Kiểm thử

Trên bench (cần bật một lần: `bench --site shd.localhost set-config allow_tests true`):

```bash
bench --site shd.localhost run-tests --app smart_helpdesk
```

Bộ kiểm thử tích hợp chạy trên site Docker kiểm thử:

```powershell
python scripts/tests/run_business_checks.py
```

Yêu cầu site thử `shd-test.localhost` đã cài ERPNext và smart_helpdesk. [business_validation.json](data/business_validation.json) ghi phạm vi live ERP/MariaDB, HTTP và calendar tests. Conformance AI offline không phải bằng chứng nghiệp vụ runtime.

## Cấu trúc

```text
apps/smart_helpdesk/          Custom app, schema, commands, permissions, Desk UI, tests
docs/design/                 Thiết kế nghiệp vụ, contracts, kiến trúc, sơ đồ
docs/implementation/         Ánh xạ thiết kế → code, cài đặt và vận hành
docker/compose.business.yml   Mount app vào các process ERP local
docker/install_business_app.py   Installer Docker (backup + install-app chuẩn)
scripts/tests/               Runner kiểm thử tích hợp
legacy/                      Lớp script demo giữa kỳ đã đóng băng (xem legacy/README.md)
data/                        Bằng chứng kiểm thử và snapshot demo theo tên file
```

## Thiết kế

[Tổng quan](docs/design/00_tong_quan_he_thong.md) · [Yêu cầu](docs/design/01_phan_tich_doanh_nghiep_va_yeu_cau.md) · [10 module](docs/design/readme.md) · [Domain/workflow](docs/design/05_domain_workflow_contracts.md) · [Deployment mục tiêu](docs/design/07_kien_truc_trien_khai.md) · [Sổ sơ đồ](docs/design/diagrams/index.html).

## Bộ demo lịch sử

```powershell
python run_pipeline.py --legacy-demo
```

Chỉ dùng để tái hiện demo cũ. Lệnh sử dụng `.env`, tạo/thay đổi dữ liệu mẫu và chạy các script Issue/Asset/kho/tài chính/KPI cũ; đây không phải luồng vận hành mới. Snapshot và tỷ lệ gán cố định không chứng minh hệ thống đạt thiết kế.
