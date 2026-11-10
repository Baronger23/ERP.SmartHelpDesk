# Legacy — Demo giữa kỳ (ĐÃ ĐÓNG BĂNG)

Thư mục này chứa lớp script của **bản demo giữa kỳ**: các script Python đứng ngoài
ERPNext, gọi REST API để dựng dữ liệu và nghiệp vụ trên các DocType gốc
(Issue, Asset, Asset Maintenance, SLA gốc, Custom Field, Client Script,
Assignment Rule).

Trạng thái: **đóng băng từ 2026-11-10**. Không phát triển thêm, không dùng cho
hệ thống hiện hành. Chỉ giữ lại làm hồ sơ lịch sử để đối chiếu khi trình bày.

Hệ thống hiện hành là app Frappe chuẩn tại `apps/smart_helpdesk/`
(28 DocType SHD riêng, cài bằng `bench install-app smart_helpdesk` —
xem README ở thư mục gốc repo).

## Nội dung

- `setup/01–06` — dựng dữ liệu nền, kỹ thuật viên, custom fields, SLA & gói bảo trì,
  quick actions, phân quyền (theo cách làm cũ, qua REST API).
- `scenarios/` — các kịch bản vận hành đầu-cuối của bản demo.
- `reports/` — báo cáo KPI của bản demo.

Muốn chạy lại bản demo cũ (chỉ để xem lịch sử): dùng Docker như trước và chạy
`python run_pipeline.py --legacy-demo` từ thư mục gốc repo.
