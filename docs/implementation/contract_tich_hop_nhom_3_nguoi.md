# Contract tích hợp cho nhóm 3 người

Phiên bản đề xuất `0.1` · 24/11/2026 · Đối chiếu mã nguồn tại `d175103`.

## 1. Phạm vi áp dụng

Tài liệu này chốt điểm giao giữa các task trong [bảng phân công](phan_cong_3_nguoi_hoan_thien_du_an.md). Người 1 là **Bạn**, người 2 là **Thành viên 2**, người 3 là **Thành viên 3**. Mỗi người có thể xây giao diện và test bằng dữ liệu mẫu trước khi đầu cung cấp API hoàn thành.

Các dòng ghi **Hiện có** mô tả hành vi đã đọc từ mã. Các dòng ghi **Đề xuất** xác định giao diện cần hiện thực trong task tương ứng. Ví dụ có ID `DEMO-*` là dữ liệu tổng hợp. Chúng dùng làm đầu vào mock và phải thay bằng ID do fixture/site trả về khi gọi ERP thật.

Các giao diện đề xuất trong tài liệu chưa tồn tại tại mốc `d175103`. Phiên bản `0.1` dùng để hai bên cung cấp/tiêu thụ cùng review và triển khai lát đầu. Khi ghép lát đó, ghi commit và phiên bản contract đã nghiệm thu trong PR. Những task không chạm điểm còn mở có thể bắt đầu ngay.

Tài liệu này bổ sung chi tiết tích hợp cho [hợp đồng domain/workflow](../design/05_domain_workflow_contracts.md). Schema hiện có nằm trong `schema.py` và JSON DocType. Khi phát hiện khác biệt giữa thiết kế mục tiêu và runtime, ghi khác biệt trong PR trước khi thay hành vi gọi API.

## 2. Quyền sở hữu dữ liệu và code

| Dữ liệu hoặc thành phần | Người giữ nghiệp vụ | Bên tiêu thụ chính | Ranh giới ghi |
|---|---|---|---|
| Customer/site, Agreement, Entitlement, Contact Authority | Bạn, M01 | Hai thành viên, portal | Công bố/thu hồi qua command. Snapshot quyền lợi của ca được giữ nguyên khi hợp đồng mới có hiệu lực. |
| Request, Incident, WorkSource, WO, Visit, Time Log, Acceptance, Wait Interval | Thành viên 2, M02/M03 | Bạn làm portal; Thành viên 3 làm vật tư/charge | Chủ workflow kiểm trạng thái. Khôi phục và nghiệm thu phát fact qua command hiện có, projection M02 cập nhật trong transaction hiện tại. |
| Equipment, PM Plan/Occurrence, Finding | Thành viên 2, M04 | Thành viên 3 dùng model; Bạn làm AI | Finding có owner. Việc tạo ca sửa đi qua classify/create_work_order. |
| Reservation, Material Use, Compatibility và chứng từ kho liên quan | Thành viên 3, M05 | Thành viên 2 làm KTV/lịch | Giữ hàng, chuyển kho và tiêu hao có command kiểm khóa/quyền. Bin/Stock Ledger native là sổ tồn. |
| Demand, MR/PO/PR và ETA cung ứng | Thành viên 3, M06 | Thành viên 2 làm lịch/cảnh báo | ETA cung ứng do mua hàng cập nhật. ETA xử lý yêu cầu vẫn thuộc Wait Interval của M02. |
| Estimate, Charge, liên kết Sales Invoice/Payment Entry | Thành viên 3, M07 | Bạn làm portal; Thành viên 2 làm KPI | Duyệt khách qua authority, PO qua manager; submit/thanh toán theo native và guard của SHD. |
| KPI Snapshot, công thức và operational queue | Thành viên 2, M08 | Quản lý, kế toán | Snapshot có kỳ/as_of/source, revision mới giữ bản cũ. Quyền tài chính do M10 kiểm. |
| Knowledge, nguồn/model/version/publish/revoke | Thành viên 3, M09 | Bạn làm AI-1 | M09 giữ catalog và metadata nguồn. Agent lấy bằng chứng qua API đọc theo phiên KTV. |
| Grant, quyền native, File, audit, runner/migration và cấu hình dịch vụ | Bạn, M10 | Cả nhóm | Chủ task đề xuất thay đổi trong PR; Bạn tích hợp các file chung để tránh migration/schema lệch. |
| AI model adapter, run, prompt, UI và kiểm nguồn | Bạn | KTV | Quyền gọi API lấy từ phiên xác thực. Model trả nhận định và nguồn trong tập bằng chứng đã cấp. |

Tổ chức file đề xuất cho API đọc mới gồm `portal_queries.py` do Bạn giữ, `service_queries.py` do Thành viên 2 giữ và `supply_queries.py`, `finance_queries.py` do Thành viên 3 giữ. Logic command hiện có tiếp tục ở module hiện tại. Việc chọn file là tổ chức trong cùng custom app Frappe.

## 3. Quy ước dữ liệu dùng chung

### 3.1. Định danh và kiểu

- ID liên kết là `name` của DocType, giữ nguyên chuỗi do server trả. `equipment_code` là mã tra máy ở API AI-1. Trường `site` là ID `SHD Site`; site Bench dùng cho vận hành/test là khái niệm riêng.
- `company`, `customer`, `site`, `warehouse` từ client là bộ lọc hoặc mục tiêu thao tác. Server xác minh quan hệ và quyền của user đăng nhập.
- Số lượng/đơn giá/số tiền của DTO đọc **mới** là chuỗi decimal, ví dụ `"1.000"`, `"120.00"`, kèm `uom`/`currency`. Tính toán phía server bằng Decimal. Giữ nguyên kiểu trả hiện tại của command khi chưa có adapter phiên bản mới.
- Ngày là `YYYY-MM-DD`. Timestamp của DTO mới dùng ISO 8601 có offset. Phản hồi kèm `timezone` của site và `observed_at` UTC. Adapter chuyển timestamp naive của ERP theo timezone site trước khi xuất.
- `null` nghĩa chưa xác định/chưa có dữ liệu, `"0"` là số 0 đã xác định. Danh sách rỗng nghĩa đọc thành công và không có mục hợp lệ trong scope hiện tại.
- Boolean là JSON `true`/`false`. Enum dùng đúng tên trong contract, UI dịch nhãn hiển thị. Trường lạ trong payload mới bị từ chối.

### 3.2. SourceRef

Mọi đường drill-down dùng đối tượng `SourceRef` có `doctype`, `name`, `revision`, `modified`. Trường `revision` là số nguyên của SHD hoặc `null` với chứng từ native; `modified` là timestamp native hoặc `null` khi chưa có. Với SHD, ít nhất `revision` phải có. Với native, ít nhất `modified` phải có. Server chọn doctype từ allowlist và kiểm quyền khi mở nguồn.

SourceRef hỗ trợ truy nguồn. Các command duyệt vẫn dùng binding hash và kiểm trạng thái riêng; một SourceRef không đủ để cho phép ghi.

```json
{
  "doctype": "SHD Work Order",
  "name": "DEMO-WO-A",
  "revision": 4,
  "modified": null
}
```

### 3.3. Envelope của API đọc mới

Frappe bọc kết quả thành `{"message": ...}`. Thành phần bên trong cho các API đọc mới trong mục 6 có dạng dưới đây. `contract_version`, `observed_at`, `timezone`, `data` đều bắt buộc. API danh sách thêm `page` với `offset`, `limit`, `has_more`.

```json
{
  "message": {
    "contract_version": "1.0",
    "observed_at": "2026-11-24T02:00:00+00:00",
    "timezone": "Asia/Ho_Chi_Minh",
    "data": {"items": []},
    "page": {"offset": 0, "limit": 20, "has_more": false}
  }
}
```

Giới hạn đề xuất là `limit` từ 1 đến 100, mặc định 20; `offset` không âm, mặc định 0. Thứ tự có khóa phụ `name` để ổn định khi cùng timestamp. `has_more` dựa trên dữ liệu đã lọc quyền, đọc dư một dòng. Dữ liệu có thể đổi giữa hai trang; lượt làm mới quay về offset 0. Caller không suy ra tổng toàn công ty từ trang của user.

AI context hiện có tiếp tục dùng envelope riêng trong [contract AI-1](ai1_erp_context.md), gồm `items/has_more` và giới hạn 5. Khi gặp `contract_version` không hỗ trợ, client báo cần cập nhật thay vì đoán cấu trúc.

## 4. Giao thức ghi và lỗi hiện tại

### 4.1. Hiện có — Business commands

```http
POST /api/method/smart_helpdesk.api.execute
Content-Type: application/json
```

```json
{
  "command": "decide_estimate",
  "payload": {
    "estimate": "DEMO-ESTIMATE-A",
    "binding_hash": "hash-returned-by-server",
    "approve": true,
    "reason": "Đồng ý phạm vi và giá hiển thị"
  },
  "idempotency_key": "portal-decision-demo-001"
}
```

- Phiên browser dùng session + CSRF. Token cá nhân chỉ dùng ở client/server đã có cấu hình được phép. User/role/scope có hiệu lực lấy từ credentials.
- Key dài 8–160 ký tự, tạo một lần cho một ý định ghi. Retry sau timeout giữ nguyên user, command, key và payload. Payload đổi là ý định mới sau khi giải quyết kết quả cũ.
- Receipt unique theo user/command/key. Payload khác với cùng key trả `IDEMPOTENCY_CONFLICT`; receipt cũ được kiểm lại scope trước replay.
- `core.result()` trả `doctype`, `name`, `status`, `revision`. Một số command trả thêm ID chứng từ native. Không coi `name` luôn là WO.
- `prepare_invoice` trả Sales Invoice **docstatus 0** và danh sách charge. Bước submit native tạo docstatus 1, hủy tạo docstatus 2. `approve_purchase_order` thực hiện submit PO sau kiểm hash. `consume` tạo Material Use và Stock Entry đã submit.
- `transfer_reserved` trả reservation **ở kho đích**, cùng `stock_entry`. UI phải thay ID giữ chỗ cho các lần consume tiếp theo.
- Chỉ công bố UI thành công sau receipt hợp lệ. Không tự đổi trạng thái hồ sơ từ dữ liệu form trước khi server xác nhận.
- Trong một command, domain changes, receipt và SHD Event nằm trong transaction Frappe. Caller server gọi nội bộ cần quản lý commit/rollback như entry point của mình. Tránh commit một phần giữa chuỗi validation và ghi.

### 4.2. Lỗi

| Tình huống | Hiện có ở runtime | Caller xử lý |
|---|---|---|
| Guest/credentials sai, role/scope không đủ | Frappe 401/403 tùy tầng | Báo đăng nhập/không truy cập được, bỏ dữ liệu nhạy cảm cũ trên UI. |
| Validation/trạng thái/đối số không hợp lệ | Thường HTTP 417, `exc_type`/thông báo Frappe | Giữ dữ liệu form để sửa hoặc tải lại hồ sơ. |
| Key cũ với nội dung khác | 417, thông báo `IDEMPOTENCY_CONFLICT` | Đối soát thao tác cũ trước khi gửi ý định mới. |
| Deadlock/query timeout được command bắt | 417, thông báo `CONCURRENCY_CONFLICT` | Transaction rollback; retry có giới hạn với cùng key/payload. |
| Không đủ stock/hold đã hết hạn | Validation, có trường hợp thông báo `INSUFFICIENT_STOCK` | Đọc lại vật tư, hiển thị thiếu; người dùng quyết định bước tiếp. |
| Estimate/authority lỗi thời | Validation hoặc PermissionError tùy nhánh | Đọc lại phiên bản/thẩm quyền, xin quyết định phù hợp. |
| Kết nối timeout sau gửi write | Client chưa biết kết quả | Gửi lại cùng key; receipt chống ghi lặp. |

Các DTO **đề xuất** dùng mã lỗi ổn định `RESOURCE_UNAVAILABLE`, `INVALID_ARGUMENT`, `CONTRACT_VERSION_UNSUPPORTED` trong trường `error_code` của response lỗi do server tạo, cùng HTTP 403/417 tương ứng. Mã nghiệp vụ mới như `STALE_VERSION` chỉ trở thành contract thực thi khi task cung cấp có code và test. Các client hiện tại vẫn phải hỗ trợ lỗi Frappe nêu trên. Nội dung traceback chỉ dùng ở môi trường phát triển có quyền.

## 5. Bất biến giữa các module

1. WorkSource thuộc đúng một nguồn Incident/Request/PM Occurrence. Work order liên kết qua WorkSource, không join đoán trực tiếp một trường equipment trên WO.
2. Lịch/kỹ năng/vật tư kiểm lại ở server khi assign/start_visit. Kết quả API đọc trước đó chỉ hỗ trợ người điều phối chọn phương án.
3. M03 ghi sự kiện khôi phục/nghiệm thu, M02 cập nhật projection/đóng yêu cầu qua logic hiện có. M07 lập hóa đơn khi WO đã khách nghiệm thu và phí hợp lệ.
4. Wait Interval giữ reason/owner/ETA. Cấu hình hiện tại `No pause` giữ đồng hồ SLA chạy; đổi ETA không đổi deadline SLA.
5. Hold qua `expires_at` vẫn tính vào held cho tới lệnh release/transition. Giao diện có thể hiển thị hết hạn, nhưng không tự tăng available. Hàng vào kho xe vẫn còn tồn; Material Issue mới làm giảm tồn theo tiêu hao.
6. Hàng quarantine được tách khỏi hàng dùng được. Tổng PO đã nhận tốt + lỗi không đủ để kết luận demand đã đáp ứng.
7. Estimate duyệt gắn nội dung/hash/expiry và authority, tái kiểm khi thực hiện. Thay scope/giá/lượng dẫn tới phiên bản phù hợp, giữ lịch sử quyết định.
8. Invoice dịch vụ luôn `update_stock=0`. Revenue KPI lấy chứng từ submitted; draft không làm tăng doanh thu. Thanh toán và hoàn tiền giữ quan hệ kế toán native.
9. Bài học/SOP có model/phiên bản/hiệu lực/quyền nguồn. Publish/revoke phản ánh vào lượt đọc mới; log hoặc cache không cấp lại quyền đã thu hồi.
10. Các read mới dùng get_list/query có permission hoặc kiểm scope từng nguồn tương đương. Server không trả toàn bộ rồi nhờ browser lọc.

## 6. Các contract liên nhóm

### IC-01 — Portal khách đọc trạng thái và quyết định chi phí

**Đề xuất** · Cung cấp Bạn với Thành viên 3 cung cấp phần estimate · Dùng Bạn làm A03, Thành viên 2 làm B02.

Endpoint `POST smart_helpdesk.portal_queries.get_request`. Input chỉ có `request` bắt buộc, ID SHD Request. Kiểm quyền Request trước khi đọc các liên kết.

`data` gồm `request`, `work_orders`, `active_waits`, `estimate`, `actions`. Request gồm `source` SourceRef, `status`, `subject`, `equipment` SourceRef hoặc null, `response_due`, `restoration_due`, `restored_at`, `accepted_at`. Các mốc thời gian nullable. Work order gồm `source` SourceRef và `status`. Active wait gồm `source`, `reason`, `owner`, `eta`, `started_at`; không gộp nhiều wait thành một ETA giả.

`estimate` nullable, có `source` SourceRef, `status`, `binding_hash`, `expires_at`, `currency`, `amount`, `lines` gồm `item/quantity/rate`. Chỉ xuất khi caller đọc được Finance của estimate. Nếu không được cấp, trường bằng null. `actions` chỉ gồm boolean `approve_estimate`, `reject_estimate`, `accept_work` để hướng dẫn UI. Server vẫn kiểm lại command ngay khi ghi. Nhiều WO/estimate phải gắn đúng nguồn, chỉ trả phần user đọc được.

Write dùng `receive_request`, `decide_estimate`, `accept_work` hiện có. Server xác minh hash từ estimate thực và authority của người dùng. Tập test gồm một khách có Service + Finance + authority, một khách chỉ Service, khách B truy Request A và estimate cũ sau khi đã lập bản mới.

### IC-02 — M05 cấp thông tin vật tư cho lịch điều phối và KTV

**Đề xuất** · Cung cấp Thành viên 3 · Dùng Thành viên 2, task B03/B04/C01/C02.

Endpoint `POST smart_helpdesk.supply_queries.get_material_readiness`. Input gồm `work_order_id` bắt buộc và `needed_at` timestamp có offset bắt buộc, là thời điểm cần giữ hàng qua đó. Kiểm scope WO và Inventory theo từng kho. Nếu user thiếu quyền cho một kho trong tập yêu cầu, trả lỗi chung RESOURCE_UNAVAILABLE cho lượt đọc; không lược kho rồi kết luận sẵn sàng.

`data` gồm `work_order` SourceRef, `needed_at`, `ready`, `items`. Mỗi item có `item`, `warehouse`, `uom`, `required_qty`, `actual_qty`, `held_qty`, `available_qty`, `reserved_for_work_order_qty`, `shortage_qty`, `reservations`. Các lượng là decimal string.

`reservations` gồm `source` SourceRef, `status`, `remaining_qty`, `expires_at`, `usable_through_needed_at` boolean. `held_qty` giữ semantics runtime mục 5. `reserved_for_work_order_qty` chỉ tính hold trạng thái Held/Partially consumed, đúng WO/item/kho và expiry lớn hơn needed_at. `shortage_qty = max(0, required_qty - reserved_for_work_order_qty)`. `ready` true khi tất cả shortage bằng 0. WO chưa khai vật tư trả `items=[]`, `ready=true` theo baseline hiện tại.

Write dùng `declare_materials`, `reserve`, `transfer_reserved`, `consume`, `release_reservation`. Ví dụ `required=2`, `actual=3`, `held=2`, `available=1`, WO đang giữ hợp lệ 1 thì thiếu 1. Test thêm hold hết hạn còn held, kho ngoài scope, chuyển reservation sang xe, hai người tranh tồn và consume cạnh tranh với release.

### IC-03 — M06 cấp cung ứng và ETA cho M02/M03

**Đề xuất** · Cung cấp Thành viên 3 · Dùng Thành viên 2, task C03/B02/B07.

Endpoint `POST smart_helpdesk.supply_queries.get_supply_status`. Input gồm `work_order_id` bắt buộc. `data` gồm `work_order` SourceRef và `demands`. Mỗi demand có `source` SourceRef, `item`, `warehouse`, `uom`, `requested_qty`, `ordered_qty`, `accepted_qty`, `rejected_qty`, `usable_allocated_qty`, `remaining_to_fulfil_qty`, `eta` ngày nullable và `documents` SourceRef[]. Mọi lượng là decimal string.

`requested_qty` là nhu cầu gốc của demand; `usable_allocated_qty` là lượng dùng được đã có căn cứ đáp ứng demand, gồm tồn được phân bổ thực và phần nhận tốt được phân bổ. `remaining_to_fulfil_qty = max(0, requested_qty - usable_allocated_qty)`. Tổng tồn kho hiện tại hoặc open PO chưa nhận không tự trở thành lượng đã đáp ứng. Phần mua bù phải truy được demand gốc và chứng từ liên quan.

Baseline chưa có allocation đầy đủ để suy `usable_allocated_qty` cho mọi lịch sử. Adapter trả null cho trường này và remaining khi thiếu căn cứ, UI hiện cần đối soát. Ca fixture đã chốt có tồn ban đầu 1 dành cho nhu cầu, demand 5, PO 4, nhận tốt 3/lỗi 1 phải kết luận còn thiếu 1. C03 chịu trách nhiệm lưu căn cứ phân bổ cho luồng này trước khi nghiệm thu, phối hợp migration mục 9.

Write **đề xuất** `update_demand_eta(demand, expected_revision, eta, reason)` qua `api.execute`, role AIS Purchasing hoặc AIS Service Manager, Inventory operate đúng scope. `expected_revision` là số nguyên dương, `eta` là Date, `reason` bắt buộc. Lock demand, kiểm revision và trạng thái chưa kết thúc, ghi ETA + actor/reason/audit, tăng revision, trả core.result. Revision sai từ chối STALE_VERSION, payload cũ cùng key replay receipt theo giao thức chung.

M02 chỉ hiển thị ETA mua như một nguồn cung ứng. Cập nhật ETA xử lý khách dùng thao tác wait/end_wait của M02 hoặc command mới được thiết kế riêng. Test mua trễ, đổi ETA hai người cạnh tranh, PO nhận đủ tổng nhưng còn thiếu hàng dùng được và việc mua bù không nhân demand.

### IC-04 — M07 cấp tài chính cho KPI, portal kế toán

**Đề xuất** · Cung cấp Thành viên 3 · Dùng Thành viên 2 và Bạn, task C04/B06/A03.

Endpoint `POST smart_helpdesk.finance_queries.get_work_order_finance`. Input `work_order_id` bắt buộc. Yêu cầu quyền đọc Service và Finance trong scope, vai trò Service Manager hoặc Billing Accountant. Endpoint dành cho nghiệp vụ kế toán, dữ liệu estimate khách xem đi qua IC-01.

`data` gồm `work_order` SourceRef, `currency`, `charges`, `invoices`. Charge gồm `source` SourceRef, `status`, `source_type`, `source_name`, `billing_policy`, `quantity`, `rate`, `cost` nullable, `invoice` SourceRef nullable. Invoice gồm `source` SourceRef, `docstatus` 0/1/2, `currency`, `net_total`, `grand_total`, `outstanding_amount`, `payment_sources` SourceRef[].

Native SourceRef phải kiểm cả quyền native và quan hệ SHD/scope. Payment Sources chỉ trả allocation liên quan invoice này. Giữ riêng từng invoice, không cộng khác currency. Snapshot KPI tiếp tục tính theo reporting.py; B06 hiển thị kết quả snapshot, dùng read mới để drill-down và đối chiếu.

Write dùng `propose_estimate`, `reconcile_charge`, `prepare_invoice`, `cancel_service_invoice` hiện có. Submit invoice và Payment Entry theo entry point native đã được A02/C04 nghiệm thu quyền. Luồng bỏ draft cần C04 chốt cách giải phóng charge trước khi công bố UI xóa/hủy draft. Test draft không ghi revenue, submit có revenue, trả một phần còn công nợ, cancel điều chỉnh snapshot mới và invoice giữ update_stock=0.

### IC-05 — M09 cấp bằng chứng cho AI-1

**Hiện có** · Cung cấp Bạn giữ API; Thành viên 3 giữ catalog · Dùng Bạn làm A04/A05, task C06.

Endpoint `POST smart_helpdesk.ai_context.get_context`, input `equipment_code`, `question`. Cấu trúc đầy đủ và mock nằm trong [contract AI-1](ai1_erp_context.md) và [JSON mẫu](ai1_erp_context.example.json). Giữ version `1.0`, lọc nguồn theo phiên KTV, model và hiệu lực. Các timestamp nghiệp vụ hiện có vẫn theo timezone site như tài liệu endpoint.

Catalog mẫu chung dùng ACC-R1, một SOP đã review, một SOP draft, một revoked, một hết hạn, một chưa tới hiệu lực, một sai model và một cùng model của khách B. Lịch sử có ca sửa và finding PM. ID thực lấy từ fixture.

M09 gọi publish/revoke qua command hiện có. UI agent xử lý `has_more`, `content_truncated` và nguồn mâu thuẫn. Mọi ID dẫn nguồn phải thuộc bằng chứng hợp lệ. Nguồn thu hồi bị loại ở lượt đọc sau. Agent đang xử lý dài cần đọc/kiểm lại nguồn trước khi công bố câu trả lời nếu quyền/nguồn đã đổi. Test ngữ cảnh rỗng, injected instruction trong SOP, citation giả, timeout và cache khác scope.

### IC-06 — Queue dịch vụ và PM cho UI/notification

**Đề xuất** · Cung cấp Thành viên 2 · Dùng Bạn làm portal và Thành viên 2 làm B02/B05/B07.

Endpoint `POST smart_helpdesk.service_queries.list_attention_items`. Input tùy chọn `customer`, `site`, `owner`, `kinds`, `offset`, `limit`; mặc định kinds gồm REQUEST, PM, FINDING. Bộ lọc được whitelist, owner là user ID và scope vẫn theo phiên.

`data.items` mỗi dòng có `source` SourceRef, `kind`, `company`, `customer`, `site`, `owner` nullable, `status`, `due_at` nullable, `due_kind`, `attention`, `waits`. `due_kind` thuộc RESPONSE/RESTORATION/PM_ORIGINAL/FINDING/null. `attention` thuộc OVERDUE/DUE_SOON/MISSING_DATA/WAITING. `waits` dùng cấu trúc active_waits IC-01, [] khi không áp dụng. Dòng Request có thể xuất hiện một lần mỗi due_kind, khóa UI là doctype/name/due_kind.

Chỉ chọn nghĩa vụ chưa hoàn tất; response đã phản hồi và restoration đã khôi phục được đánh giá bằng thời điểm hoàn thành khi làm KPI. PM dùng due_original, giữ due_adjusted ở trang chi tiết. Ngưỡng DUE_SOON cấu hình theo loại và timezone, ví dụ trong fixture là cấu hình kiểm thử. Không có deadline thì MISSING_DATA. Thứ tự OVERDUE, DUE_SOON, MISSING_DATA, WAITING rồi due_at/name; null xếp cuối trong cùng nhóm.

Nguồn queue là dữ liệu nghiệp vụ hiện hành. UI có thể refresh để xem thay đổi. Notification kiểm lại tình trạng nghĩa vụ và quyền người nhận trước khi gửi. Test đủ deadline/ngày nghỉ, nhiều wait, owner đổi, ca hoàn tất và phân trang sau lọc quyền.

### IC-07 — Cảnh báo qua job và nhận diện sự kiện

**Đề xuất** · Thành viên 2 giữ job B07, Bạn giữ quyền/cấu hình A06; Thành viên 3 cung cấp supply IC-03 và Agreement do Bạn cung cấp.

Một candidate cảnh báo gồm `source` SourceRef, `rule` enum SLA_RESPONSE/SLA_RESTORATION/SUPPLY_ETA/PM_DUE/FINDING_DUE/AGREEMENT_EXPIRY, `due_at`, `recipient` user ID, `bucket` khóa kỳ nhắc đã cấu hình và `permission_scope` company/customer/site. Dedup key gồm source.doctype/source.name/rule/due_at/recipient/bucket. Revision không nằm trong dedup key để thay ghi chú không gửi lại cùng cảnh báo.

Job dùng user dịch vụ được cấu hình, đọc nguồn trong scope, tính recipient và kiểm quyền recipient trước khi tạo notification riêng tư. Ghi dấu đã tạo cùng transaction với notification qua unique key. Mốc B07 ưu tiên thông báo trong app. Nếu thêm email, cần trạng thái gửi, retry và provider receipt ở task kênh email để xử lý lỗi sau commit.

Không consumer nào cần một broker mới cho lát triển khai này. Nguồn fact đã có là SHD Event và chứng từ ERPNext. SHD Event hiện có `event_type`, `aggregate_type`, `aggregate_id`, `aggregate_version`, `occurred_at`, `recorded_at`, `actor`, `command_id`, `supersedes_event`, payload JSON. Mapping tên sự kiện phải lấy từ command, ví dụ ReservationConsumed, WorkOrderRestored, CustomerAcceptanceRecorded, InvoiceSubmitted. Các projection hiện tại giữ giao dịch đồng bộ đã có.

Test chạy job hai lần, restart, quyền người nhận thu hồi, due_at đổi, đổi owner và hoàn tất nguồn trước giờ gửi. Một key hợp lệ chỉ tạo một notification trong app.

### IC-08 — Quyền bootstrap và tài khoản dùng chung cho nghiệm thu

**Hiện có một phần; đề xuất thu hẹp cấu hình** · Bạn cung cấp A01/A02/A06 · Cả nhóm dùng.

Fixture hiện có tạo các user acc.* và một số role native cần để ERP map chứng từ. Cấu hình triển khai cần bảng role/grant tối thiểu theo hành động, không sao chép nguyên grant All của fixture vào staging.

| Persona | Hành động kiểm giao diện | Nguồn kiểm quyền bắt buộc |
|---|---|---|
| Customer A | Gửi/theo dõi, quyết định estimate, nghiệm thu | Service/Finance đúng khách/site, authority riêng Approve Cost/Accept đúng hạn/hạn mức. |
| Customer B | Làm với dữ liệu B, thử ID A | Cả API, native nguồn liên quan, file/export của A bị chặn. |
| Dispatcher | Triage, booking, PM, queue | Service và Inventory tối thiểu phục vụ điều phối trong scope được giao. |
| Assigned technician | Visit, công, tiêu hao, đọc SOP/AI | Service đúng WO phân công, Inventory đúng kho, Knowledge đúng nguồn; xử lý gate estimate mà giữ giới hạn trường tài chính. |
| Warehouse keeper | Reserve/transfer/receive | Inventory đúng kho, quyền Service cần để kiểm quan hệ và role native cần thiết. |
| Purchasing | Demand/MR/PO draft, ETA | Inventory/Service đúng nguồn; role native cho mapping; duyệt PO thuộc manager. |
| Accountant | Estimate/charge/invoice/payment | Finance + Service/Inventory cần cho nguồn; native Accounts; cost chỉ cấp đối tượng phù hợp. |
| Manager/reviewer | Duyệt PO, goodwill, công bố catalog | Role đúng thao tác và grant đúng tài nguyên; quyết định khách vẫn cần authority tương ứng. |

Ghi matrix đã chốt vào artifact cấu hình trước khi kiểm endpoint liên nhóm. Test role native rộng nhưng thiếu grant SHD và user đã disable. Lỗi quyền phải sửa bằng phạm vi được xác định hoặc kiểm quyền hẹp ở workflow, có test hồi quy.

## 7. Làm song song bằng mock và contract test

### 7.1. Bộ mẫu tối thiểu cho từng interface

Mỗi người cung cấp API mới đặt mẫu dưới `docs/implementation/contracts/<IC-ID>/` trong PR triển khai của mình. Gói bàn giao gồm schema request/response JSON Schema 2020-12, các file mẫu JSON và test HTTP thật. Required fields/enum/nullability trong mục 3/6 phải khớp schema. Input dùng additionalProperties=false; output cho phép caller bỏ qua trường thêm tương thích.

Các trường hợp cần có gồm success, empty, forbidden, stale và timeout mô phỏng phù hợp endpoint. API list thêm nhiều trang. Với IC-02 bổ sung expired_hold và transfer; IC-03 thêm rejected_receipt; IC-04 thêm draft/submitted/cancelled/partial_payment. IC-05 kế thừa JSON mẫu đã có và bổ sung ca negative trong bộ đánh giá AI.

Schema và fixture mới sẽ được người cung cấp thêm ở PR từng interface. Ở bản `0.1`, các cấu trúc được quy định trong tài liệu này và JSON mock AI-1 đã có để bắt đầu ngay. Không tuyên bố các interface mới đã chạy ERP.

### 7.2. Cách chia việc ngay

- Bạn làm portal dựa trên IC-01 mẫu, AI theo IC-05, quyền IC-08; đồng thời giữ runner/schema tích hợp.
- Thành viên 2 viết queue/lịch/KTV/PM/KPI bằng IC-02/03/04 mock; cung cấp IC-06 và job IC-07.
- Thành viên 3 làm IC-02/03/04 trước, corpus IC-05 song song chuẩn bị dữ liệu, rồi nối UI thương mại.
- Mỗi UI dùng cùng một adapter cho mock và HTTP. Khi endpoint đã đạt schema/permission test, đổi cấu hình adapter và chạy consumer test với dữ liệu thật.
- Provider kiểm schema, quyền, invariant và transaction. Consumer kiểm hiển thị null/empty/error/version và sử dụng đúng ID receipt. Nhóm chạy integration theo ba luồng khi cả hai đầu đã sẵn sàng.

### 7.3. Dataset liên nhóm

Dùng Company SHD Acceptance, ACC Customer A/B, ACC-EQ-001/ACC-R1, kho chính và kho quarantine theo fixture hiện có. Đổi ID tự sinh thành tham chiếu do fixture báo. Các persona lấy từ tests/acceptance.py, KTV B lấy từ tests/ai_context.py.

Các ca chuẩn gồm billable A, PM finding A, khách B truy A, demand 5/tồn phân bổ 1/mua 4/nhận tốt 3+lỗi 1, estimate hết hạn, authority hết hạn, hold hết hạn, invoice draft/submit/partial payment và SOP revoked. Chạy trên site thử hoặc staging có dữ liệu tổng hợp.

## 8. Những quyết định còn mở cần chốt theo task

| Mã | Điểm cần quyết định | Người đề xuất | Bên bị ảnh hưởng | Cách tiến hành trong lúc chờ |
|---|---|---|---|---|
| D01 | Tự release hold hay thủ công sau quá hạn; tần suất và cạnh tranh | Thành viên 3, C02 | B03/B04, service user A06 | Dùng semantics hiện tại, hiện quá hạn và thao tác release có quyền. |
| D02 | Lưu allocation để kết luận thiếu/đủ demand, thay unique và nhiều chứng từ mua | Thành viên 3, C03 | B02/B07, migration | Read DTO có null khi chưa đối soát; UI làm bằng ca mẫu đã xác định. |
| D03 | Luồng invoice nháp bỏ dở và mở lại charge | Thành viên 3, C04 | Portal, KPI, audit | Luồng draft → submit hiện có vẫn dùng; chưa hiển thị hành động bỏ nháp mới trước khi có command. |
| D04 | Ngưỡng nhắc, receiver và khoảng nhắc lại | Thành viên 2, B07 | A01/A06, dữ liệu hợp đồng | Dùng cấu hình thử có nhãn, viết test dedup trước. |
| D05 | Model/provider, giới hạn và quyền log AI | Bạn, A04/A05 | Corpus M09, vận hành | Adapter model giả lập và JSON context cho UI/test. |
| D06 | Quyền Finance tối thiểu khi KTV consume WO có estimate | Bạn, A02; Thành viên 3 review | B04/C01, dữ liệu nhạy cảm | Tái hiện fixture hiện tại, bổ sung test che trường và role trước khi thu hẹp. |

Các quyết định này chỉ ảnh hưởng task liên quan. Người giữ module ghi phương án và cập nhật contract/fixture trong PR, bên tiêu thụ review trước khi ghép. Dùng mở rộng schema/API theo phiên bản thay vì sửa ngầm ý nghĩa trường đã dùng.

## 9. Versioning, migration và môi trường

- Thêm trường output optional giữ major version. Xóa/đổi kiểu/đổi đơn vị/đổi semantics/nullability/enum mà client đang dùng cần version mới và kế hoạch adapter chuyển tiếp. Đồng bộ schema, fixture và caller trong PR liên quan.
- Command mới được đăng ký qua handlers trong api.py, có role và test catalog. Hiện handlers chỉ nhập các module nghiệp vụ cố định; đặt command ở file mới cần tích hợp registry này trước khi gọi qua HTTP.
- Dữ liệu cũ thiếu trường mới cần được backfill hoặc trả null có semantics rõ. Trường required/unique mới cần migration có kiểm dữ liệu xung đột trước khi siết ràng buộc. Chạy migrate hai lần và thử nâng từ d175103.
- Bạn tích hợp các thay đổi schema.py, JSON DocType/generator, hooks, permission và runner. Mỗi module giữ test và fixtures của mình, tránh hai PR chỉnh cùng một bootstrap dữ liệu theo hai cách.
- Bench dùng chung thì một lượt dựng lại site thử tại một thời điểm. Mỗi lượt ghi rõ site/cổng/app path và theo dõi process do lượt đó sở hữu. Cấu hình --port của runner hiện tại cần đối chiếu HTTP smoke còn hardcode 8000 trước khi dùng cổng khác.
- Khi chạy các test baseline, runner còn ghi environment DB theo chuỗi cấu hình hiện có; A06 cập nhật nhận diện phiên bản thật. Chưa dùng chuỗi đó làm bằng chứng version DB.

## 10. Cổng nghiệm thu các điểm giao

| Mã | Hai đầu cần có bằng chứng | Kết quả cần đạt |
|---|---|---|
| CT-01 | Portal + estimate/authority | Khách A thấy đúng hash/giá, duyệt được, B bị chặn, bản cũ/hết hạn bị từ chối. |
| CT-02 | Lịch/KTV + inventory | Ready theo needed_at đúng, transfer dùng ID hold đích, consume giảm tồn một lần, hold hết hạn không bị hiểu là đã release. |
| CT-03 | Supply + queue/notification | Ca 3 tốt + 1 lỗi còn thiếu 1 có căn cứ, ETA mua tách ETA xử lý, job không gửi trùng. |
| CT-04 | Invoice/payment + KPI | Draft không có doanh thu, submit/cancel tạo nguồn đúng, payment một phần có outstanding đúng, cost không lộ ngoài quyền. |
| CT-05 | Catalog + AI | Đúng model/phiên bản/scope, revoked bị loại, nguồn giả/injected instruction không thành hành động, nguồn mâu thuẫn được báo. |
| CT-06 | PM/Visit/Finding + WorkSource | Sinh lại không trùng, PM nhiều finding, ca Repair đi đúng nguồn, lịch sử đủ dữ liệu để agent/UI dẫn. |
| CT-07 | Service job + recipient permissions | Đổi owner/thu hồi quyền/hoàn thành trước gửi được tái kiểm; duplicate chỉ tạo một notification. |
| CT-08 | Migration + cả ba nhánh | Migrate hai lần, chứng từ cũ đọc/tiếp tục được, runner và smoke UI liên nhóm đạt. |

Mỗi PR ghi contract ID, version, người cung cấp/tiêu thụ, schema/fixture đã cập nhật, ca provider/consumer đã chạy và các quyết định còn mở. Tài liệu này cùng bảng phân công là đầu vào để tạo task, theo dõi phụ thuộc và review thay đổi liên module.

## Phụ lục — Danh mục command hiện có tại d175103

Danh mục dưới đây được trích từ hàm có decorator command trong mã nguồn để đối chiếu tên và tham số. Tất cả được cộng quyền AIS Service Manager theo decorator hiện tại; role và scope vẫn phải cùng hợp lệ. Đây là signature runtime, các kiểu nhập/đầu ra đặc thù tham chiếu mã nghiệp vụ và các contract ở trên. Catalog HTTP chỉ trả subset phù hợp vai trò đăng nhập.

| Signature | Role khai báo, cộng Service Manager | Module |
|---|---|---|
| `register(record_type, values)` | AIS Dispatcher, AIS Field Technician, AIS Knowledge Reviewer | `operations.py` |
| `activate(record_type, name)` | AIS Knowledge Reviewer | `operations.py` |
| `revoke(record_type, name, reason)` | AIS Service Manager | `operations.py` |
| `receive_request(company, customer, site, subject, reported_at, received_at, service_type='Repair', equipment=None)` | AIS Dispatcher, AIS Customer Portal | `operations.py` |
| `triage(request, priority, reason, owner, agreement=None, incident=None)` | AIS Dispatcher | `operations.py` |
| `acknowledge(request, response, occurred_at)` | AIS Dispatcher | `operations.py` |
| `create_work_order(origin_kind, origin, scope_text, package_key='MAIN', required_for_restoration=True)` | AIS Dispatcher | `operations.py` |
| `assign(work_order_id, technician, starts_at, ends_at, required_skill)` | AIS Dispatcher | `operations.py` |
| `start_visit(work_order_id, occurred_at)` | AIS Field Technician, AIS Dispatcher | `operations.py` |
| `finish_visit(visit, outcome, evidence, occurred_at, completed=True)` | AIS Field Technician | `operations.py` |
| `log_time(visit, hours, billable_hours, work_kind)` | AIS Field Technician | `operations.py` |
| `restore(work_order_id, criteria, measurements, occurred_at)` | AIS Field Technician | `operations.py` |
| `accept_work(work_order_id, evidence, occurred_at)` | AIS Customer Portal, AIS Dispatcher | `operations.py` |
| `close_request(request, reason)` | AIS Dispatcher | `operations.py` |
| `wait(request, reason, owner, eta)` | AIS Dispatcher | `operations.py` |
| `end_wait(interval)` | AIS Dispatcher | `operations.py` |
| `classify_callback(incident, original_incident, classification, reason)` | AIS Dispatcher | `operations.py` |
| `correct_restoration(work_order_id, source_event, reason, occurred_at=None)` | AIS Dispatcher | `operations.py` |
| `generate_pm(plan, period_key)` | AIS Dispatcher | `maintenance.py` |
| `postpone_pm(occurrence, new_due, reason)` | AIS Dispatcher | `maintenance.py` |
| `complete_pm(occurrence, observations, findings, occurred_at)` | AIS Field Technician, AIS Dispatcher | `maintenance.py` |
| `classify_finding(finding, disposition, reason)` | AIS Dispatcher | `maintenance.py` |
| `search_knowledge(company, model, query, customer=None, site=None)` | AIS Knowledge Reviewer, AIS Field Technician, AIS Dispatcher | `maintenance.py` |
| `declare_materials(work_order_id, requirements)` | AIS Dispatcher | `inventory.py` |
| `available_stock(work_order_id, item, warehouse)` | AIS Warehouse Keeper, AIS Dispatcher, AIS Field Technician | `inventory.py` |
| `reserve(work_order_id, item, warehouse, quantity, expires_at)` | AIS Warehouse Keeper, AIS Dispatcher | `inventory.py` |
| `release_reservation(reservation, reason)` | AIS Warehouse Keeper, AIS Dispatcher | `inventory.py` |
| `consume(reservation, visit, quantity)` | AIS Warehouse Keeper, AIS Field Technician | `inventory.py` |
| `transfer_reserved(reservation, target_warehouse, quantity)` | AIS Warehouse Keeper | `inventory.py` |
| `create_demand(work_order_id, item, warehouse, quantity, needed_at)` | AIS Purchasing, AIS Dispatcher | `inventory.py` |
| `requisition(demand)` | AIS Purchasing | `inventory.py` |
| `prepare_purchase_order(demand, supplier, rate, delivery_date)` | AIS Purchasing | `inventory.py` |
| `approve_purchase_order(demand, binding_hash, reason)` | AIS Service Manager | `inventory.py` |
| `receive_purchase(demand, accepted_quantity, rejected_quantity='0', rejected_warehouse=None)` | AIS Warehouse Keeper | `inventory.py` |
| `propose_estimate(work_order_id, lines, currency, expires_at)` | AIS Billing Accountant, AIS Dispatcher | `commercial.py` |
| `decide_estimate(estimate, binding_hash, approve, reason)` | AIS Customer Portal | `commercial.py` |
| `reconcile_charge(source_type, source_name, item, rate, billing_policy, labor_cost_rate=None, reason=None)` | AIS Billing Accountant | `commercial.py` |
| `prepare_invoice(work_order_id, selling_price_list=None)` | AIS Billing Accountant | `commercial.py` |
| `cancel_service_invoice(invoice, reason)` | AIS Service Manager | `commercial.py` |
| `snapshot_kpis(company, period_start, period_end, customer=None, site=None, as_of=None, supersedes=None, auto_revision=False)` | AIS Billing Accountant | `reporting.py` |
