# Lộ trình, quyết định mở và đối chiếu triển khai

Phiên bản 3.0: bổ sung [domain/workflow](05_domain_workflow_contracts.md) và [9 tài liệu AI](ai_architecture/readme.md). Conformance offline không là kết quả runtime ERP/LLM.

## 1. Vị trí của repository trong thiết kế

Chỉ ở bước này mới đối chiếu nhu cầu với mã hiện có. Phạm vi kiểm tra là đọc repository và snapshot, chưa chạy hệ thống sống. “Có mã” không bằng “đã đạt yêu cầu”, và “chưa có mã” không có nghĩa doanh nghiệp không cần tính năng đó.

## 2. Khoảng cách theo module phiên bản 2

| Module | Có thể tái dùng | Khoảng cách quan trọng | Bằng chứng cần có |
|---|---|---|---|
| M01 hợp đồng | Customer, SLA hai hạng và custom_customer | Site/authority, coverage/version/snapshot còn thiếu | Ca áp đúng version ngày hiệu lực và khách duyệt đúng quyền |
| M02 tiếp nhận | Tạo Issue, incident_time, priority/SLA | Timeline, triage có căn cứ, wait/duplicate/deadline version | Các mốc giữ đúng, lịch ngoài giờ và nhánh thiếu dữ liệu |
| M03 tác nghiệp | User/Team, rules, quick actions và assignment API | Work order/visit, availability, time log/acceptance/callback | Ca nhiều visit, gán thật, kết quả và review |
| M04 máy/PM | Asset/Location, plans/logs, link custom_issue, QR | Equipment accounting boundary, checklist/occurrence/findings | PM nhiều findings, version, hoãn và QR đúng máy |
| M05 vật tư | Item/Warehouse/Bin, receipts/transfers/issues | Reservation, custody/return, concurrent availability | Giữ chỗ tranh chấp, dùng/trả và quyền kho |
| M06 mua hàng | MR-PO-PR và van transfer sample | Demand net, partial/reject, approval/ETA | Nhu cầu không lặp, nhận một phần và hàng bị reject |
| M07 tài chính | Ba ca warranty/billable/goodwill, invoice link | Estimate/approval/charge source/allocation/adjustment | Phí được duyệt, nguồn công/vật tư không trùng |
| M08 KPI | Report đọc dữ liệu và JSON dashboard | Công thức, source histories, scope/kỳ/phân trang | Dataset có thất bại, tử/mẫu và source list |
| M09 tri thức | Thiết kế Knowledge Domain v3 | Catalog/version/lesson/ingestion/hybrid retrieval/freshness chưa có runtime | Nguồn duyệt và retrieval/model/scope evaluation |
| Agent Harness ngang | 9 tài liệu, schemas, registry, fixtures và checker offline | Chưa có orchestrator/state/gateway/LLM adapter hoặc ERP transaction implementation | Durable resume, crash/permission/approval integration, task evaluation |
| M10 kiểm soát | Role/User Permission/Custom DocPerm setup | Effective scope, field/file, maker-checker/audit/restore | Persona tests và recovery drill |

## 3. Những dấu hiệu không được diễn giải thành kết quả đạt

- scenarios/05 tự gán người sau tạo Issue; assignment đúng trong snapshot không chứng minh engine theo chuyên môn đúng.
- PM log được nối Issue trong script mẫu; chưa có workflow phát hiện nhiều findings và phân loại hành động.
- custom_incident_time tồn tại, nhưng chưa có bộ tính SLA theo mốc đó và lịch đã kiểm chứng; cần giữ anchor khác nhau.
- verification_evidence có resolution_by null và stock_before/after cùng 10, reorder_condition false; chưa đủ bằng chứng deadline/trigger thấp tồn. Nguyên nhân có thể chạy lại hoặc trạng thái sau bổ sung, chưa có history để kết luận.
- Report gán các tỷ lệ 100%, overdue=0 và số công cố định, không đủ đánh giá vận hành.
- Pipeline dùng Custom Fields trước bước tạo trường; site đã cấu hình có thể chạy, cài mới chưa bảo đảm.
- Finance script dùng ID Issue cố định và dữ liệu công/giá mẫu; không đủ làm engine quyết toán tổng quát.
- Quick Action “In Progress”, giá trị field HTML QR và việc scope Role cộng quyền cần thử trên version ERPNext mục tiêu.

Nguồn mã: [pipeline](../../run_pipeline.py), [client API](../../scripts/core/frappe_client.py), [setup](../../scripts/setup), [scenarios](../../scripts/scenarios), [report KPI](../../scripts/reports/generate_kpi_dashboard.py). Các tệp data là snapshot demo, không số hiện thời của doanh nghiệp.

## 4. Kế hoạch triển khai theo lát cắt giá trị

| Giai đoạn | Lát cắt | Đầu ra review | Cổng nghiệm thu |
|---|---|---|---|
| A: xác nhận doanh nghiệp | Chuỗi giá trị, người có quyền, cam kết/fee/callback/PM | PP confirmed/rejected, baseline, policy register | Không biến giả thuyết thành kết luận khảo sát |
| B: nền tảng dữ liệu/quyền | Customer/site/máy, scope, version tối thiểu, setup | Danh mục có ownership, cấu hình mới có thể lặp | Không lộ khách/kho/file; validation server |
| C: ca sửa xuyên suốt | WorkSource/snapshot → request → work order/visit → atomic hold → restored/accept → phí/approval P1 | Một ca và nhánh chờ/lỗi có nguồn | Ownership M03/M02 đúng, approval/version/hash và retry |
| D: PM và bổ sung | Occurrence/finding → ca; shortage → MR/PO/partial receipt | Hai luồng phụ kết nối ca lõi | Hạn gốc giữ, không mất finding, không mua lặp |
| E: chất lượng và đo lường | Callback, time log, cost/report/source | Dataset đúng/trễ/thiếu mốc/tái phát và drill-down | Công thức có tử/mẫu, không tỷ lệ hardcode |
| F: Knowledge và Agent Harness | Hybrid retrieval; single orchestrator/state/tools/HITL/evaluation | E2E read/approved draft và recovery dataset | Contracts → integration → evaluation → pilot; không R3 baseline |

Không tự đưa timeline theo tuần nếu chưa biết nhân lực, lịch môn học và năng lực hạ tầng. Với đồ án, ưu tiên chứng minh lát cắt C/D với kiểm soát, rồi ghi minh bạch các tính năng mục tiêu chưa triển khai.

## 5. Sổ quyết định nghiệp vụ cần chốt

| Quyết định | Vì sao ảnh hưởng nhiều module? | Người xác nhận |
|---|---|---|
| SLA anchor/lịch/pause/khôi phục tạm | M01 quyền lợi, M02 deadline, M03 event, M08 công thức | Quản lý dịch vụ và đại diện khách |
| Callback window và cách phân loại | M03 review, M07 miễn phí, M08 FTFR | Trưởng nhóm và quản lý hợp đồng |
| Người duyệt phía khách, mức goodwill/mua | M01 authority, M07 phí, M06 PO, M10 policy | Quản lý khách và tài chính |
| Cấp trước hay tiêu hao ngay, serial/core return | M05 ledger, M03 time/visit, M07 cost | Thủ kho và trưởng nhóm |
| PM due gốc/hoãn/cửa sổ máy dừng | M04 kế hoạch, M03 lịch, M08 PM rate | Quản lý bảo trì và khách |
| Equipment kỹ thuật trên Asset hay DocType riêng | M04 dữ liệu, M07 accounting boundary | Kiến trúc sư và kế toán |
| Cost allocation/doanh thu/overhead | M07 ledger, M08 margin | Kế toán/quản lý |
| RPO/RTO/retention/permission export | M10 vận hành, M08/09 dữ liệu | Quản trị và chủ dữ liệu |

Khi chưa chốt, ghi trạng thái open, thiết kế dùng tham số và ca kiểm thử tương ứng; không lấy giá trị mã demo làm chính sách mặc định đã phê duyệt.

## 6. Đánh giá phạm vi và rủi ro thực hiện

Rủi ro chính là tạo quá nhiều giao diện nhưng chưa bảo đảm dữ liệu, hoặc đặt AI trước khi có SOP nguồn. Cách giảm: triển khai một ca end-to-end với state/event/source rõ, dùng dữ liệu có nhánh thất bại, khóa idempotency và persona testing trước khi mở rộng UX.

Một work order/incident và hợp đồng chính đơn giản có thể là giới hạn MVP; thiếu multi-contract hoặc tổ đội nên ghi giới hạn, không khẳng định enterprise full. Việc module chia thành 10 bản không yêu cầu 10 nhóm phát triển hay 10 dịch vụ deploy.

Điều kiện review thiết kế: mọi tính năng có PP/US; nguồn dữ liệu và người quyết định rõ; happy/error path có AC; diagram dùng cùng tên/mã; module/data/state không mâu thuẫn. Điều kiện review triển khai thêm code, kết quả kiểm tra và bằng chứng runtime theo AC.

## 7. Đóng góp ý phiên bản 3 ở mức thiết kế

| Góp ý | Quyết định / artifact | Trạng thái |
|---|---|---|
| M09 gộp knowledge/runtime | M09 Knowledge Domain + Harness ngang, 9 tài liệu AI | Đã phân ranh |
| Approval P1/P2 | Version/hash/authority/expiry bắt buộc P1; P2 routing sâu | Thiết kế đã chốt, chưa test ERP |
| Reservation lõi nhưng P2 | Atomic reservation P1; DC-05/HT-15 oracle | Concurrency thật chưa test |
| PM/request/incident source thiếu | WorkSource XOR FKs và source/package/generation unique | ER/module đã sửa; chưa migration |
| Restored/Accepted hai owner | M03 facts/acceptance; M02 projections/closure | Authority contract đã có |
| AI draft thiếu transaction | Prepare/approve/revalidate/commit+receipt/outbox/reconcile | 26 offline vectors; chưa adapter |
| KPI late/correction | Event time/watermark/as_of/snapshot revisions/supersedes | Consumer runtime chưa test |

## 8. Lát cắt AI và gates

A1 scoped reads/tri thức/planning/evidence với state/limits/observability; A2 prepare/HITL/approved business draft qua custom gateway có idempotency receipt; A3 crash/recovery/security/holdout evaluation rồi pilot. Reservation thực, submit, override vẫn do workflows nghiệp vụ. Multi-agent chỉ sau chứng cứ single-orchestrator baseline không đáp ứng task/context/isolation.

Kết quả hiện có: [conformance report](ai_architecture/contracts/conformance_results.json), scope offline. Chưa chạy HT integration với ERP hoặc model thực; Gate A không thay Gates B-D ở [observability/evaluation](ai_architecture/08_observability_and_evaluation.md).
