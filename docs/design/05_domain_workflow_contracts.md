# Hợp đồng domain và workflow chuẩn hóa

Phiên bản 3.0 · 08/10/2026. Tài liệu này là nguồn chuẩn cho ranh giới, sự kiện và bất biến; sơ đồ ER và các module phải tuân thủ. Đây là hợp đồng mục tiêu, chưa là migration hoặc kiểm thử ERPNext đã chạy.

## 1. Nguồn công việc chung

Một work order phải có một `WorkSource` chuẩn thuộc một trong ba loại:

| origin_kind | Đối tượng nguồn | Khi dùng | Không được làm |
|---|---|---|---|
| INCIDENT | Incident đã được triage | Sửa chữa khắc phục, kể cả finding từ PM | Tạo thêm work source từ từng request báo cùng incident |
| SERVICE_REQUEST | Request không gắn incident | Tư vấn, kiểm tra hoặc dịch vụ theo yêu cầu | Gán nguồn request và incident đồng thời |
| PM_OCCURRENCE | Một kỳ PM đến hạn | Gói việc bảo trì định kỳ | Dùng Plan tổng thay occurrence cụ thể |

`WorkSource` có ID ổn định, kind, source_version và đúng một FK `incident_id`, `service_request_id`, `pm_occurrence_id`. Server kiểm tra kind tương ứng FK và nguồn tồn tại/cùng phạm vi. Request đã liên kết incident phải dùng nguồn incident để không nhân đôi việc khi nhiều người báo.

Work order có `source_id`, `package_key`, `generation_version`, scope/tasks và `required_for_restoration`. Nguồn có thể nhiều gói việc riêng; retry tạo cùng gói/phiên bản trả lại cùng ID. Gói bổ sung phải có quyết định scope; đổi số generation không phải cách lách chống trùng.

### Ràng buộc logic bắt buộc

- XOR ba FK nguồn: đúng một khác null; kind khớp FK.
- UNIQUE WorkSource.incident_id, WorkSource.service_request_id, WorkSource.pm_occurrence_id cho các giá trị không null.
- UNIQUE WorkOrder(source_id, package_key, generation_version).
- UNIQUE PMOccurrence(plan_version_id, equipment_id, period_key).
- PM mặc định dùng package_key=`PM_MAIN`; generation_version lấy từ phiên bản scope đã duyệt của occurrence.
- Tạo bổ sung/chuyển nguồn phải qua validation và quyết định, không overwrite source của work order đã thực hiện.

Các unique phải ở database, validation phía ứng dụng không đủ chống hai worker tạo đồng thời. Cách khai báo nullable unique/check/FK cần thử trên database/ORM mục tiêu; chưa cung cấp SQL để chạy tự động.

## 2. Quyền sở hữu sự kiện và trạng thái

| Sự kiện/fact | Nguồn có thẩm quyền | Bên phản chiếu | Điều kiện |
|---|---|---|---|
| VisitStarted / VisitCompleted | M03 | M02/M08 | Người, visit, thời điểm và outcome hợp lệ |
| WorkOrderRestored | M03 | M02/M08 | Scope kỹ thuật và tiêu chí thử máy đã đạt |
| CustomerAcceptanceRecorded | M03 | M02/M07/M08 | Người phía khách đúng thẩm quyền; accepted/rejected/pending rõ |
| IncidentRestorationProjected | M02, tính từ facts M03 | Portal/M08 | Tất cả gói bắt buộc hiện hành đã restored; giữ event nguồn |
| ServiceRequestClosed | M02 | M08 | Kết quả/phân loại/acceptance theo policy của request |
| PMOccurrenceCompleted / FindingClassified | M04 | M03/M02/M08 | Checklist/kết quả; findings giữ outcome riêng |
| ReservationHeld / Released | M05 | M03/M08 | Transaction tồn và giữ chỗ hợp lệ |
| EstimateApproved / ChargeReconciled / InvoiceSubmitted | M07 | M02/M03/M08 | M10 quyết định quyền; M07 sở hữu version/phạm vi phí |

M02 không tự ghi bằng chứng thử máy hoặc acceptance thay M03. M03 không tự đóng request hoặc sửa SLA. Một trạng thái portal là projection có `source_event_ids` và version; không phải fact thứ hai có thể sửa độc lập.

Work order: Planned → Assigned → Accepted → In progress → Technically complete → Customer accepted → Closed, Waiting/Cancelled có reason. Visit: Scheduled → Started → Completed/Incomplete/Cancelled. Request: Received → Triage → Ready → Active → Restored → Accepted → Closed hoặc Rejected/Cancelled/Duplicate. Incident projection chỉ dùng facts của các work order required; Completed visit chưa đủ WorkOrderRestored.

Correction hoặc reopening tạo event mới tham chiếu event bị thay thế và lý do; không xóa mốc cũ. Hóa đơn/thu tiền là trạng thái thương mại độc lập; request không mặc định chờ khách trả tiền mới được đóng kỹ thuật.

## 3. Quyết định P1 về vật tư và approval

**P1 có reservation atomic**, không chọn mô hình chỉ cấp trực tiếp làm baseline. Gán/hẹn ca có nhu cầu hàng phải kiểm tra availability; giữ chỗ áp dụng theo item/kho/work order. Transfer không đồng nghĩa tiêu hao. Không có giữ chỗ atomic thì tính năng “cam kết vật tư cho nhiều ca” chưa được nghiệm thu, không chuyển nó sang P2 nhưng vẫn dùng trong hành trình lõi.

Transaction giữ chỗ khóa hoặc kiểm tra CAS số dư/holds của item-kho, xác nhận available >= requested, ghi hold và tăng version, ghi idempotency result cùng commit. Hai request cùng nhìn thấy tồn 2 rồi xin giữ 2 không cùng được Held. Khi retry, dùng cùng key và payload; key cũ với payload khác bị conflict.

**P1 có approval phát sinh tối thiểu bắt buộc**: estimate version/phạm vi/số tiền, approver có thẩm quyền, approved hash, trạng thái và hạn. Scope/giá đổi sau duyệt phải xin duyệt lại. KTV không thực hiện phần vượt đã duyệt chỉ vì workflow ngoại lệ nâng cao dự kiến P2. Chính sách khẩn được định nghĩa/duyệt trước; nếu chưa có, quay về pending approval.

P2 bổ sung routing nhiều cấp, delegation, ngưỡng phức tạp, lịch nhắc và xử lý tranh chấp. Nó không trì hoãn gate approval của P1. Approval AI sử dụng cùng authority M10 và object/version của M07/M05/M06, không lập một đường duyệt ít kiểm soát hơn.

## 4. Event envelope và giao nhận

```json
{
  "event_id": "evt-001",
  "event_type": "WorkOrderRestored.v1",
  "aggregate_type": "WorkOrder",
  "aggregate_id": "WO-001",
  "aggregate_version": 8,
  "occurred_at": "2026-10-08T09:00:00+07:00",
  "recorded_at": "2026-10-08T09:02:00+07:00",
  "actor_id": "user-tech-01",
  "correlation_id": "corr-001",
  "causation_id": "command-001",
  "supersedes_event_id": null,
  "payload_ref": "evidence://wo-001/restoration-8"
}
```

Event ID chống xử lý trùng; aggregate_version bảo vệ thứ tự; occurred_at khác recorded_at. Outbox trong cùng transaction nghiệp vụ phát sự kiện sau commit; consumer inbox unique event_id. Không khẳng định broker vận chuyển exactly once. Nếu chỉ gọi server nội bộ, vẫn phải bảo toàn event identity và projection.

## 5. KPI, event đến muộn và sửa mốc

M08 lưu snapshot với event-time window, processed watermark, source versions, công thức/policy và `as_of`. Event đến muộn được đưa vào revision mới cho các kỳ chịu ảnh hưởng; báo cáo đã phát không bị overwrite không dấu vết. Chính sách provisional/final và khoảng chốt kỳ là tham số nghiệp vụ cần xác nhận, không tự đặt 7 ngày cho mọi KPI.

Correction chỉ định supersedes_event_id; chỉ fact hiệu lực tại as_of được tính, không cộng cả bản cũ và mới. Consumer xử lý event trùng không nhân đôi tử/mẫu. Late callback có thể đổi FTFR kỳ của ca gốc; snapshot mới nêu lý do và delta. Forecast/tỷ lệ tạm phải mang nhãn provisional; chưa đủ cửa sổ không tính đạt.

Khi event về đảo thứ tự, giữ pending/reconcile theo aggregate version hoặc rebuild từ facts authoritative; không suy rằng event mới nhất theo received time là đúng nhất. Nếu không có lịch sử đầy đủ, ghi không đủ dữ liệu để tái tạo kỳ.

## 6. Hợp đồng kiểm thử domain

| ID | Setup / kích thích | Oracle bắt buộc |
|---|---|---|
| DC-01 | Tạo PM_MAIN hai lần cho cùng occurrence/version | Một WorkSource và một work order, cùng ID khi retry |
| DC-02 | Tư vấn không có incident; sửa có hai request cùng incident | Tư vấn có nguồn request; ca sửa không nhân đôi theo hai tin báo |
| DC-03 | Work order có hai visits, chỉ một completed | Request không tự restored nếu scope bắt buộc chưa đạt |
| DC-04 | Khách duyệt estimate A rồi scope đổi B | B không được thực hiện theo approval A |
| DC-05 | Hai hold 2 trên stock 2, concurrent | Một success, một conflict/insufficient, total held <= 2 |
| DC-06 | M03 phát restored rồi sửa fact có correction | M02/M08 projection đổi có version; fact cũ vẫn truy được |
| DC-07 | Một event giao hai lần, callback đến muộn | Không đếm lặp; kỳ liên quan có revision, delta và lý do |

DC là oracle cho triển khai ERP tương lai; bộ checker AI offline chỉ kiểm tra những hợp đồng AI được nêu trong [observability/evaluation](ai_architecture/08_observability_and_evaluation.md), không thay DC runtime.

## 7. Xử lý các góp ý và giới hạn

Nguồn work order chung, ownership technical facts, P1 approval/reservation và KPI late events được chốt ở mức thiết kế này. Tính đúng của khóa, ORM/FK, outbox và permission epoch còn phải chứng minh khi hiện thực. Agent Harness là runtime ngang, không thêm module nghiệp vụ M11; [kiến trúc AI](ai_architecture/01_agent_harness_architecture.md) quản execution chứ không sở hữu facts ERP.
