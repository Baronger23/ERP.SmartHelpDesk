# Smart HelpDesk & Maintenance

Hệ thống dịch vụ bảo trì công nghiệp B2B trên ERPNext/Frappe. Custom app `apps/smart_helpdesk` hiện thực lõi nghiệp vụ theo bộ thiết kế v3. Agent Harness và tích hợp AI được hoãn; catalog tri thức kỹ thuật dùng độc lập.

## Vận hành local

Khởi động ERPNext Docker hiện có, rồi cài/cập nhật app:

```powershell
python run_pipeline.py
```

Lệnh backup DB + files, cài app và migrate trên site Docker `frontend`, không triển khai Cloud. Mở [workspace Smart Helpdesk](http://localhost:8080/desk/smart-helpdesk), dùng **Tạo hồ sơ** và **Thao tác nghiệp vụ**.

[Hướng dẫn triển khai và vận hành](docs/implementation/business_modules.md) mô tả cấu hình scope/authority, policy SLA, chuỗi nghiệp vụ, API, giới hạn và phần chưa triển khai. Cần cấu hình khách/site/máy, hợp đồng, người duyệt và quyền trước vận hành; dữ liệu demo không tự thành chính sách đã duyệt.

## Module nghiệp vụ

M01 khách hàng/hợp đồng · M02 tiếp nhận/SLA · M03 điều phối/tác nghiệp · M04 thiết bị/PM · M05 kho/reservation · M06 mua hàng · M07 chi phí/hóa đơn · M08 báo cáo/KPI · M09 catalog tri thức · M10 quyền/audit.

Request, incident, work order và visit có dữ liệu riêng. Reservation kiểm tra đồng thời trên Bin native. Approval gắn nội dung/version/expiry, mua/kho/hóa đơn dùng chứng từ ERPNext native; command và journal có transaction/idempotency. Tài liệu triển khai phân biệt thiết kế mục tiêu với mức hiện thực.

## Kiểm thử

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
scripts/setup/install_business_app.py   Installer có backup
scripts/tests/               Runner kiểm thử tích hợp
scripts/setup/, scenarios/   Bộ cấu hình và kịch bản demo lịch sử
data/                        Bằng chứng kiểm thử và snapshot demo theo tên file
```

## Thiết kế

[Tổng quan](docs/design/00_tong_quan_he_thong.md) · [Yêu cầu](docs/design/01_phan_tich_doanh_nghiep_va_yeu_cau.md) · [10 module](docs/design/readme.md) · [Domain/workflow](docs/design/05_domain_workflow_contracts.md) · [Deployment mục tiêu](docs/design/07_kien_truc_trien_khai.md) · [Sổ sơ đồ](docs/design/diagrams/index.html).

## Bộ demo lịch sử

```powershell
python run_pipeline.py --legacy-demo
```

Chỉ dùng để tái hiện demo cũ. Lệnh sử dụng `.env`, tạo/thay đổi dữ liệu mẫu và chạy các script Issue/Asset/kho/tài chính/KPI cũ; đây không phải luồng vận hành mới. Snapshot và tỷ lệ gán cố định không chứng minh hệ thống đạt thiết kế.
