# Triển khai nghiệp vụ trên ERPNext

Ngày cập nhật: 15/10/2026. Nguồn yêu cầu: `docs/design` v3 và hợp đồng domain/workflow. Mã thực thi: `apps/smart_helpdesk`, chạy trong Frappe; không phải backend ERP riêng.

## Ánh xạ module

| Module | Năng lực hiện thực | Nguồn chính |
|---|---|---|
| M01 | Site, thẩm quyền khách, hợp đồng có phiên bản/hiệu lực, coverage, entitlement snapshot | SHD Site, Contact Authority, Agreement, Entitlement; Customer native |
| M02 | Reported/received/recorded, triage, lịch SLA/timezone/ngày nghỉ, phản hồi, chờ/ETA, projection và đóng sau nghiệm thu | SHD Request, Incident, Wait Interval |
| M03 | WorkSource XOR, gói việc chống trùng, kỹ năng/khả dụng, chống đặt lịch trùng, nhiều visit, công thực/tính phí, thử máy, nghiệm thu, callback/correction | SHD Work Source, Work Order, Technician, Visit, Time Log, Acceptance |
| M04 | Equipment kỹ thuật tách Asset kế toán, checklist theo version plan, kỳ PM chống trùng, hoãn giữ hạn gốc, số đo/đơn vị, nhiều finding có owner | SHD Equipment, PM Plan, PM Occurrence, Finding |
| M05 | Bin native, atomic reservation, kiểm vật tư đã khai trước hẹn, transfer/custody, tiêu hao tại visit, release phần chưa dùng | SHD Reservation, Material Use, Compatibility; Stock Entry/Bin/Stock Ledger native |
| M06 | Demand nguồn WO, chống mua trùng, MR draft, PO theo MR, duyệt đúng hash, nhận một phần và cách ly hàng reject | SHD Demand; MR/PO/Purchase Receipt native |
| M07 | Estimate version/hash/expiry, khách đúng quyền duyệt, thay estimate vô hiệu bản cũ, charge theo nguồn, giá vốn khác giá bán, invoice không xuất kho lại, hủy có manager review | SHD Estimate/Charge; Sales Invoice native |
| M08 | Snapshot bất biến/as_of/watermark/source IDs, revision, SLA có tử/mẫu/thiếu dữ liệu, FTFR đủ cửa sổ, PM hạn gốc, tài chính cohort và queue cần hành động | SHD KPI Snapshot, Event; sự kiện submit/cancel invoice |
| M09 | Catalog SOP/lesson theo model/version/reviewer/hiệu lực, publish/revoke, keyword search theo quyền | SHD Knowledge; không dùng LLM/vector DB |
| M10 | Role + grant theo company/customer/site/resource/warehouse, authority có hiệu lực/hạn mức, chặn ghi trực tiếp, private files, journal/receipt chống trùng, installer có backup | SHD Access Grant, Contact Authority, Event, Command; User/Role/File native |

## Cài đặt local

Khởi động ERPNext Docker hiện có rồi chạy:

```powershell
python run_pipeline.py
# hoặc
python scripts/setup/install_business_app.py --site frontend
```

Installer chỉ thao tác cụm Docker local `frappe_docker`, không dùng `.env`/Frappe Cloud. Nó backup DB + files trước, mount source vào backend/worker/scheduler, cài package, đăng ký app, cài/migrate schema và restart process. Cập nhật dùng cùng lệnh.

Installer kiểm tra Origin browser khớp public Host tại Nginx, rồi dùng cặp Host/Origin `frontend:8080` trong Docker để realtime gọi ngược API xác thực. Điều này sửa xung đột hostname của template local mà vẫn từ chối Origin ngoài hệ thống; chạy `nginx -t` trước reload. Config trước sửa giữ ở `/etc/nginx/conf.d/frappe.conf.before-smart-helpdesk`. Chạy lại installer nếu tái tạo frontend container.

Khi tái tạo container phải dùng `docker/compose.business.yml` cùng compose gốc, với `SHD_APP_PATH` là đường dẫn tuyệt đối đến app. `docker start` giữ mount hiện có. Đây là deployment development; production phải đóng app vào image bất biến theo tài liệu deployment.

Mở [Smart Helpdesk local](http://localhost:8080/desk/smart-helpdesk). Có 10 lối vào module. Danh sách có **Tạo hồ sơ** và **Thao tác nghiệp vụ**; form là bản xem read-only, chuyển trạng thái qua lệnh server. Phía khách hiện có API kiểm quyền; portal chuyên biệt và notification chưa nằm trong đợt này.

## Cấu hình dữ liệu và quyền

1. Kiểm tra Company, Customer, Item, Warehouse, Supplier và bảng giá native. Tạo SHD Equipment cho máy khách, không tạo bút toán Asset. Dữ liệu demo cũ không tự được chuyển thành dữ liệu đã xác minh.
2. Service Manager tạo Site, Equipment, Technician, Compatibility và Agreement; duyệt công bố hợp đồng. Phải nhập thời lượng/anchor/timezone/lịch/callback window theo quyết định nghiệp vụ.
3. Contact Authority tách **Accept** và **Approve Cost** theo user/customer/site, thời gian hiệu lực và hạn mức.
4. Access Grant có `actions=read,operate`, `resource_type=Service/Inventory/Finance/Knowledge/Administration`. All chỉ dùng cho người thực sự được giao đầy đủ phạm vi. Customer/site/warehouse trống nghĩa không giới hạn chiều đó trong company.
5. Quyền kho cần grant Inventory riêng; grant Service không tự cấp mọi kho. Khách duyệt estimate cần grant Finance đúng customer/site ngoài grant Service. Role giới hạn lệnh; grant giới hạn tài nguyên. Thêm role native rộng không mở quyền trên chứng từ SHD.

Policy SLA yêu cầu `anchor` (reported_at/received_at), `timezone`, `calendar`, `response_minutes`, `restoration_minutes`, `pause_policy="No pause"`. Lịch Business hours có `weekly_windows` dạng `{ "0": [["08:00","12:00"],["13:00","17:00"]], ... }`, 0=thứ Hai đến 6=Chủ nhật, và `holidays` danh sách YYYY-MM-DD. Calendar 24x7 chỉ dùng nếu hợp đồng xác nhận phục vụ liên tục. `callback_window_hours` xác định cửa sổ quan sát; `included_items` liệt kê item được coverage miễn phí. Không lấy số demo làm chính sách mặc định.

Timestamp có offset được đổi về timezone site trước lưu; timestamp không offset được hiểu theo timezone site. Thời gian chờ hiện giữ clock chạy; chưa hỗ trợ pause có điều kiện.

## Luồng vận hành

Ca sửa: `receive_request` → `triage` → `acknowledge` → `create_work_order` → `declare_materials` nếu cần → `reserve` → `assign` → `propose_estimate`/`decide_estimate` khi phát sinh → `start_visit` → `consume`/`log_time` → `finish_visit` → `restore` → `accept_work` → `close_request`.

Thiếu hàng: `create_demand` → `requisition` → `prepare_purchase_order` → manager xem đúng nội dung/hash và `approve_purchase_order` → `receive_purchase`. Hàng reject vào kho cách ly khác kho dùng được. Baseline một demand/item trên PO/MR; không tự phân bổ cùng một PO ngoài nguồn cho nhiều ca.

PM: tạo/công bố plan → `generate_pm` với số kỳ từ 0 → công việc PM_MAIN → visit/checklist → `complete_pm` → `classify_finding`. Hoàn PM giữ findings mở. Finding Repair tạo incident riêng để điều phối tiếp.

Scheduler mặc định không chạy nghiệp vụ khi chưa có danh tính dịch vụ. Quản trị cấu hình `shd_scheduler_user` cho sinh kỳ PM và `shd_report_user` + `shd_report_lookback_days` (1–31 ngày do nghiệp vụ chọn) cho report. Không chấp nhận Administrator/Guest làm service identity. Tài khoản sinh PM cần role AIS Dispatcher + grant Service read/operate; tài khoản report cần AIS Billing Accountant và các grant Service read/Finance read,operate đúng site. Jobs dùng permission-aware queries và command keys ổn định; mỗi lượt PM sinh tối đa 50 kỳ để xử lý bù có giới hạn. Báo cáo là provisional và revise các kỳ trong lookback; sự kiện cũ hơn khoảng đó cần gọi report chủ động. Cấu hình xong, bật scheduler theo cách vận hành bench của site. Không tự cấu hình các user/quyền này từ dữ liệu demo.

Kế toán: `reconcile_charge` từ Material Use/Time Log → `prepare_invoice` chọn bảng giá cùng tiền tệ → kiểm tra và submit native. Invoice luôn `update_stock=0`. Manager dùng `cancel_service_invoice` có lý do, giữ hóa đơn canceled và mở allocation để đối soát lại. Goodwill cần manager; Warranty cần item trong snapshot coverage. Thanh toán/phải thu dùng workflow native.

## API và transaction

```text
POST /api/method/smart_helpdesk.api.execute
Authorization: token <key của user>:<secret>
Content-Type: application/json

{"command":"...", "payload":{...}, "idempotency_key":"mã ổn định 8–160 ký tự"}
```

Browser dùng session + CSRF của Frappe. GET `smart_helpdesk.api.catalog` trả lệnh/đối số được role cho phép; `master_catalog` trả loại hồ sơ được tạo. Runtime kiểm thêm scope, state và authority.

Cùng user/lệnh/key và payload trả receipt cũ; payload khác trả IDEMPOTENCY_CONFLICT. Quyền thu hồi chặn đọc receipt ngoài scope. Sau timeout không đổi key khi chưa rõ kết quả. CONCURRENCY_CONFLICT nghĩa transaction đã rollback, retry cùng key. Frappe validation trả HTTP 417, thiếu quyền trả 403; không dùng GET ghi dữ liệu.

DB unique bảo vệ source/WO/PM/charge/command; CHECK bảo vệ WorkSource XOR. Bin và reservations dùng locking/current reads trong transaction. Deadlock/serialization failure rollback toàn bộ. Journal cùng transaction, projection đồng bộ trong ERP; chưa có broker ngoài hoặc tuyên bố delivery exactly-once.

## Kiểm thử

```powershell
docker exec frappe_docker-backend-1 bench new-site shd-test.localhost --install-app erpnext --install-app smart_helpdesk
python scripts/tests/run_business_checks.py
```

Nhập DB/admin credentials local khi tạo site. Tests chỉ chấp nhận `shd-test.*`, dùng dữ liệu synthetic. Từng ca rollback; concurrency và HTTP giữ fixture trên site riêng để truy bằng chứng. Runner lưu `data/business_validation.json`, phân biệt live ERP/MariaDB, hai connection cạnh tranh, authenticated HTTP và calendar tests. Bằng chứng UI là workspace/list/dialog trên trình duyệt. Đây không phải UAT, load test, security certification hoặc restore/HA drill.

## Phần ngoài đợt triển khai

- Agent Harness, LLM, hybrid RAG/ingestion/vector DB, AI registry/checkpoint/resume/HITL: hoãn theo yêu cầu.
- Nhiều mức duyệt/delegation, SLA pause, tích hợp hotline/Zalo, tối ưu lịch/tuyến, mobile/offline, IoT: chưa triển khai.
- Scope generation mới, sửa phạm vi đã thực hiện/nghiệm thu, chuyển site equipment, serial/batch/core recovery, credit-note/charge chia nhiều invoice: cần workflow bổ sung. P1 chặn các trường hợp chưa hỗ trợ.
- Scheduler daily có sinh kỳ PM và tạo/revise báo cáo theo scope tài khoản dịch vụ được cấu hình. Chưa tự chốt kỳ hoặc gửi escalation/notification.
- Mua chưa net/allocation nhiều demand vào một PO; ngoại tệ invoice cần chính sách FX. Kho cách ly phải được quản trị như kho không dùng cấp vật tư.
- Các Issue/Asset/demo cũ và quyền native không gắn SHD còn cần audit/migration riêng; custom app không chứng minh toàn bộ bộ quyền cũ đã được sửa.
