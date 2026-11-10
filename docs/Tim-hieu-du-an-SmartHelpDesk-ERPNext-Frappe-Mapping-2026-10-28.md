# TÌM HIỂU DỰ ÁN SMART HELPDESK & MAINTENANCE TRÊN ERPNEXT / FRAPPE

**Tài liệu tổng kết để học và nắm toàn bộ dự án — viết theo góc nhìn kỹ sư ERP**

- **Dự án được đọc trực tiếp:** `E:\DUT.K1N4\HTTT\Project_SmartHelpDesk_Mainternance` (qua Tailscale + SSH, ngày 28/10/2026)
- **Repo GitHub:** `Baronger23/ERP.SmartHelpDesk`, nhánh `develop`, commit gần nhất `049ee89 feat: deployment architecture`
- **Môn học:** Hệ thống thông tin (HTTT) — doanh nghiệp giả định **AIS (Alpha Industrial Services)**, công ty dịch vụ bảo trì công nghiệp B2B: bảo hành, bảo trì định kỳ (PM) và sửa chữa sự cố cho nhà máy (bao bì, dược, nhựa, cơ khí) ở miền Trung
- **Phiên bản nền đang chạy thật (có bằng chứng kiểm thử):** Frappe Framework **v16.33.1**, ERPNext **v16.34.2**, MariaDB **11.8**, chạy Docker local tại `http://localhost:8080`, site tên `frontend`
- **Cách dùng file này:** Phần 1–2 học nền tảng (Frappe / ERPNext / DocType). Phần 3–6 học cách ERPNext cho sẵn cái gì và tùy biến ra sao. Phần 7–10 là phần quan trọng nhất: **giải phẫu chính dự án này và bảng mapping chuẩn** module nào có sẵn, module nào phải sửa/nâng cấp, module nào phải làm mới, module nào chưa làm.

> **Cảnh báo đọc hiểu số 1 — dự án này có HAI lớp triển khai khác nhau, đừng trộn:**
> 1. **Lớp demo lịch sử** (thư mục `scripts/`, chạy bằng `run_pipeline.py --legacy-demo`): cấu hình thẳng lên DocType có sẵn của ERPNext (`Issue`, `Asset`, `Asset Maintenance`…) qua REST API, cộng thêm Custom Field / Client Script / Assignment Rule. Đây là bản giữa kỳ.
> 2. **Lớp nghiệp vụ mới — thiết kế v3** (thư mục `apps/smart_helpdesk/`): một **custom app Frappe** đúng nghĩa, tự định nghĩa **28 DocType riêng (tiền tố `SHD`)**, **40 lệnh nghiệp vụ (business command)** ở server, chỉ mượn ERPNext ở những chỗ ERPNext làm tốt nhất: danh mục gốc (Customer, Item, Warehouse…), kho (Bin, Stock Entry), mua hàng (Material Request, Purchase Order, Purchase Receipt) và hóa đơn bán (Sales Invoice). Đây mới là kiến trúc hiện tại của dự án.
>
> Rất nhiều tài liệu trong `docs/` (báo cáo giữa kỳ, ma trận kiểm chứng) mô tả lớp 1; còn `README.md` gốc và `docs/implementation/business_modules.md` mô tả lớp 2. Khi ai hỏi "dự án dùng Issue hay dùng SHD Request?" — câu trả lời đúng là: **giữa kỳ dùng Issue, bản hiện tại đã chuyển sang SHD Request và bộ SHD riêng; hai lớp chưa được migrate dữ liệu qua nhau.**

---

## PHẦN 0 — TÓM TẮT MỘT TRANG CHO NGƯỜI MỚI

1. **Frappe** là *framework* (khung lập trình web full-stack, Python + JavaScript, mã nguồn mở). **ERPNext** là *một ứng dụng nghiệp vụ viết bằng Frappe* — bộ phần mềm ERP có sẵn kế toán, kho, mua, bán, tài sản, hỗ trợ khách hàng… Quan hệ: **ERPNext chạy trên Frappe**, giống như một app chạy trên hệ điều hành. Muốn sửa/thêm nghiệp vụ cho ERPNext thì viết thêm một **custom app Frappe** khác cài chung site — đó đúng là việc dự án này làm với app `smart_helpdesk`.
2. **DocType** là khái niệm trung tâm của Frappe: khai báo một DocType là đồng thời có **bảng database + form nhập liệu + màn hình danh sách + API + phân quyền**. Hiểu DocType là hiểu 70% Frappe.
3. **ERPNext cho sẵn giao diện luôn.** Giao diện tên là **Desk**: cứ có DocType là có màn hình. Dự án này **không tự viết frontend riêng** cho nghiệp vụ — nó dùng Desk, cộng một Workspace riêng và một file JavaScript (`operations.js`) để biến các form thành màn hình "chỉ xem + bấm nút thao tác nghiệp vụ".
4. **Nghiệp vụ của AIS được chia thành 10 module M01–M10** (khách hàng/hợp đồng, tiếp nhận/SLA, điều phối, thiết bị/PM, kho, mua hàng, chi phí/hóa đơn, báo cáo/KPI, tri thức, quản trị/kiểm soát). Đây là **module nghiệp vụ theo thiết kế của nhóm**, không phải module có sẵn của ERPNext — đừng nhầm hai khái niệm "module" này (xem mục 3.3).
5. **Kết luận mapping tổng thể (chi tiết ở Phần 8):**
   - **Dùng thẳng ERPNext, gần như không sửa:** danh mục Customer / Supplier / Item / Warehouse / Company, sổ kho (Bin, Stock Ledger), chứng từ mua (MR → PO → Purchase Receipt), hóa đơn bán (Sales Invoice).
   - **Có sẵn nhưng KHÔNG đủ, phải làm mới gần như thay thế:** tiếp nhận & SLA (native `Issue` + `Service Level Agreement` không có snapshot quyền lợi hợp đồng, không có mốc reported/received tách rời, không có khoảng chờ), work order hiện trường (ERPNext **không có** Field Service Work Order — `Work Order` của ERPNext là *lệnh sản xuất*), bảo trì cho **máy của khách** (native `Asset` là tài sản kế toán của chính công ty), giữ chỗ vật tư (native chỉ có tồn kho, không có reservation), dự toán phát sinh được khách duyệt theo phiên bản (native không có).
   - **Đã làm mới trong app SHD:** toàn bộ các khoảng trống trên bằng 28 DocType `SHD *` + 40 command + engine SLA theo lịch làm việc riêng + cơ chế event/command journal chống trùng lặp.
   - **Chưa làm (đã ghi rõ trong tài liệu dự án, không được nói là đã có):** portal riêng cho khách hàng, thông báo/escalation tự động, tạm dừng đồng hồ SLA (SLA pause), app mobile/offline, IoT/bảo trì dự đoán, toàn bộ runtime AI/RAG (mới có thiết kế + kiểm tra offline), duyệt nhiều cấp, tối ưu tuyến đường/lịch, migrate dữ liệu từ lớp Issue cũ sang lớp SHD, triển khai production thật (hiện mới là Docker local phục vụ dev/demo).

---

## PHẦN 1 — FRAPPE LÀ GÌ, ERPNEXT LÀ GÌ, QUAN HỆ CỦA CHÚNG

### 1.1. Nói dễ hiểu trước

Hãy hình dung 3 tầng:

```
┌─────────────────────────────────────────────────────────────┐
│  APP NGHIỆP VỤ CỦA BẠN   smart_helpdesk  (dự án này viết)   │  ← nghiệp vụ riêng của AIS
├─────────────────────────────────────────────────────────────┤
│  APP NGHIỆP VỤ CÓ SẴN    ERPNext                            │  ← kế toán, kho, mua, bán,
│                                                             │    tài sản, hỗ trợ... có sẵn
├─────────────────────────────────────────────────────────────┤
│  FRAMEWORK               Frappe                             │  ← DocType, Desk UI, phân quyền,
│                                                             │    workflow, API, scheduler, báo cáo
├─────────────────────────────────────────────────────────────┤
│  HẠ TẦNG                 MariaDB · Redis · Nginx · Python   │  ← database, cache/queue, web server
└─────────────────────────────────────────────────────────────┘
```

- **Frappe** (đọc kiểu "frappe" như món cà phê đá xay) là một **web framework full-stack** do công ty Frappe Technologies (Ấn Độ) phát triển, giấy phép MIT. Nó lo những việc "khung" mà hệ thống quản trị nào cũng cần: định nghĩa dữ liệu (DocType), giao diện quản trị (Desk), người dùng & phân quyền, workflow duyệt, đính kèm file, email/thông báo, in ấn (Print Format), báo cáo, tác vụ nền & lập lịch (scheduler), REST API, đa ngôn ngữ. Frappe **không chứa nghiệp vụ ERP nào cả** — một site chỉ cài Frappe trần sẽ chỉ có các công cụ hệ thống.
- **ERPNext** là **một app viết trên Frappe**, giấy phép GPL-3.0, chứa toàn bộ nghiệp vụ ERP: hệ thống DocType và logic kế toán, kho, mua bán, sản xuất, tài sản, hỗ trợ… Khi "cài ERPNext" thực chất là: cài Frappe trước, tạo một **site**, rồi cài app `erpnext` vào site đó.
- Cùng một "họ" còn có các app Frappe khác, cài thêm vào cùng site nếu cần: **Frappe HR / HRMS** (nhân sự, lương — đã tách khỏi ERPNext từ v14), **Frappe Helpdesk** (helpdesk hiện đại, DocType `HD Ticket`, giao diện kiểu Vue), **Frappe CRM**, **Frappe LMS**… Điểm này quan trọng cho dự án: *bản cài local của dự án chỉ có Frappe + ERPNext* — không có HRMS, không có Helpdesk (xem mapping mục 8.4).

**Ví von để nhớ:** Frappe giống **Android** (hệ điều hành + bộ công cụ), ERPNext giống **một bộ app văn phòng cài sẵn cực lớn** chạy trên Android đó, còn `smart_helpdesk` là **app riêng nhóm tự viết** cài thêm vào cùng máy, dùng chung dữ liệu và tài khoản với bộ app có sẵn.

### 1.2. Các khái niệm tổ chức của Frappe cần biết khi đọc dự án

| Khái niệm | Là gì | Trong dự án này |
|---|---|---|
| **Bench** | Một thư mục cài đặt Frappe chứa code framework + các app + các site; quản lý bằng lệnh `bench` | Bench nằm trong container Docker của bộ `frappe_docker` (thư mục anh em `E:\DUT.K1N4\HTTT\frappe_docker`, file `pwd.yml`) |
| **Site** | Một "cơ sở dữ liệu + bộ file" độc lập chạy trên bench; mỗi site là một doanh nghiệp/hệ thống riêng | Site vận hành: `frontend`; site kiểm thử: `shd-test.localhost` |
| **App** | Một gói code Frappe (có `hooks.py`, DocType, trang Desk…) cài được vào site | `frappe`, `erpnext`, và `smart_helpdesk` của dự án |
| **Module Def / Module** | Cách Frappe gom DocType thành nhóm trong một app | App của dự án có đúng 1 module: `Smart Helpdesk` (file `modules.txt`) |
| **hooks.py** | File "móc nối" của app: khai báo app này chạy hàm nào khi cài đặt, khi có sự kiện trên chứng từ, lịch chạy định kỳ… | `apps/smart_helpdesk/smart_helpdesk/hooks.py` — xem giải phẫu ở mục 7.3 |
| **migrate** | Lệnh `bench migrate`: đồng bộ định nghĩa DocType trong code xuống database | Installer của dự án luôn chạy migrate sau khi cài/cập nhật app |

### 1.3. Frappe cho sẵn những "đồ nghề" nào (để hiểu vì sao nhóm không phải tự viết)

- **Desk** — giao diện quản trị web (mục 4).
- **Hệ thống User / Role / Permission** 3 lớp: quyền theo Role trên từng DocType, **User Permission** (giới hạn theo giá trị, ví dụ chỉ thấy một Company/Warehouse), và quyền mức bản ghi/trường (permlevel).
- **Workflow** — máy trạng thái khai báo cho chứng từ (Draft → Approved → Submitted…), gắn điều kiện và vai trò.
- **Scheduler + Background Jobs** (Redis queue) — việc chạy theo lịch (daily/hourly…) và việc nền.
- **REST API mặc định** cho mọi DocType (`/api/resource/<DocType>`) và API theo hàm (`/api/method/<đường.dẫn.hàm>` khi hàm được `@frappe.whitelist()`).
- **Print Format, Report Builder, Query/Script Report, Dashboard/Number Card, Notification, Email, File đính kèm, tìm kiếm, đa ngôn ngữ, audit trail (Version)**.

> Nguyên tắc kỹ sư ERP số 1: **cái gì framework/ERPNext đã cho sẵn và đủ dùng thì cấu hình, không viết lại.** Viết lại User/Role, viết lại sổ kho, viết lại hạch toán hóa đơn… là những việc tốn công nhất và lỗi nhiều nhất. Dự án này làm đúng nguyên tắc đó ở lớp kho/mua/hóa đơn — và cố tình *không* tuân theo ở lớp ticket/work order, vì ở đó native không đủ (lý do cụ thể ở Phần 8).

---

## PHẦN 2 — DOCTYPE LÀ GÌ? GIẢI THÍCH CHO DỄ HIỂU

### 2.1. Định nghĩa một câu

> **DocType là "bản khai báo" của một loại đối tượng/chứng từ trong hệ thống. Khai một DocType, Frappe tự sinh ra: (1) một bảng trong database, (2) một màn hình danh sách, (3) một form nhập/xem, (4) API để đọc/ghi, (5) chỗ để gắn phân quyền, workflow và logic.**

Ví von: trong lập trình hướng đối tượng, DocType giống một **class**; mỗi bản ghi (ví dụ một phiếu yêu cầu cụ thể `SHD Request` số xyz) là một **instance/document**. Nhưng DocType mạnh hơn class thường ở chỗ nó là **metadata sống trong chính database**: bản thân "DocType" cũng là một DocType (định nghĩa của nó lưu trong bảng `tabDocType`, định nghĩa từng trường lưu trong `tabDocField`). Vì mọi thứ là dữ liệu, Frappe mới sinh được giao diện và API *tự động* từ cùng một nguồn khai báo.

### 2.2. Một DocType gồm những gì?

Lấy ví dụ có thật trong dự án — DocType `SHD Request` (yêu cầu dịch vụ) được khai trong `apps/smart_helpdesk/smart_helpdesk/schema.py`:

```python
"SHD Request": [
    link("equipment", "SHD Equipment"),          # máy nào bị hỏng
    link("incident", "SHD Incident"),            # thuộc sự cố nào (nếu có)
    link("entitlement", "SHD Entitlement"),      # quyền lợi hợp đồng áp tại thời điểm nhận
    field("subject", required=True),             # nội dung yêu cầu — bắt buộc
    field("service_type", "Select", "Repair\nConsultation\nPM", True),
    field("priority"),                            # mức ưu tiên
    link("service_owner", "User"),               # người chịu trách nhiệm
    field("reported_at", "Datetime", required=True),   # khách báo lúc nào
    field("received_at", "Datetime", required=True),   # AIS nhận lúc nào
    field("acknowledged_at", "Datetime"),        # đã phản hồi lúc nào
    field("response_due", "Datetime"),           # hạn phản hồi theo SLA
    field("restoration_due", "Datetime"),        # hạn khôi phục theo SLA
    ...
]
# + các trường chung mọi DocType SHD đều có (COMMON):
# company (Link→Company, bắt buộc), customer (Link→Customer), site (Link→SHD Site),
# status (Data), revision (Int — số phiên bản), details (JSON)
```

Từ khai báo này, khi app được cài/migrate, Frappe sẽ:

1. Tạo bảng MariaDB tên **`tabSHD Request`** (mọi DocType đều có tiền tố `tab`), mỗi field là một cột.
2. Tự thêm các cột chuẩn mọi DocType đều có: `name` (khóa chính/mã bản ghi), `creation`, `modified`, `modified_by`, `owner`, và nếu là chứng từ gửi duyệt thì có `docstatus` (0=Draft, 1=Submitted, 2=Cancelled).
3. Sinh trang danh sách `/desk/shd-request`, form `/desk/shd-request/<mã>`, bộ lọc, nút xuất dữ liệu…
4. Mở REST API: `GET/POST /api/resource/SHD Request`.
5. Cho phép gắn quyền theo Role ngay trong định nghĩa DocType.

### 2.3. Các loại trường (fieldtype) hay gặp nhất

| Fieldtype | Nghĩa dễ hiểu | Ví dụ trong dự án |
|---|---|---|
| `Data` | Văn bản ngắn một dòng | `subject`, `status`, `equipment_code` |
| `Small Text` / `Text` / `Text Editor` | Văn bản dài / có định dạng | `address`, nội dung SOP trong `SHD Knowledge` |
| `Select` | Chọn một trong danh sách cố định | `service_type`: Repair / Consultation / PM |
| `Link` | **Khóa ngoại** — trỏ tới một DocType khác | `customer` → `Customer`, `item` → `Item` |
| `Table` / Child Table | Bảng con nằm trong form cha (một-nhiều, không đứng độc lập) | Dòng vật tư/hóa đơn trong các chứng từ native |
| `Int` / `Float` / `Currency` / `Percent` | Số nguyên / số thực / tiền / phần trăm | `quantity`, `amount`, `cost_rate` |
| `Date` / `Datetime` / `Time` | Ngày / ngày-giờ / giờ | Toàn bộ các mốc SLA `*_at`, `*_due` |
| `Check` | Ô tick đúng/sai | `required_for_restoration` |
| `Attach` / `Attach Image` | File đính kèm | Bằng chứng hiện trường (qua DocType `File` native) |
| `JSON` / `Code` | Dữ liệu cấu trúc dạng JSON | `policy` của hợp đồng, `details`, checklist PM |
| `Link` động (`Dynamic Link`), `Password`, `Geolocation`… | Các loại đặc biệt khác | Ít dùng trong dự án này |

**Điểm mấu chốt cần nhớ khi đọc code dự án:** quan hệ giữa các đối tượng trong ERPNext/Frappe thể hiện bằng trường **Link**, không vẽ bằng "khóa ngoại SQL" thủ công. Muốn biết một DocType nối với những DocType nào, cứ đọc danh sách trường Link của nó. Sơ đồ quan hệ DocType ở Chương 4 báo cáo giữa kỳ của nhóm chính là vẽ lại các Link này.

### 2.4. Vòng đời của một bản ghi (Document)

```
Tạo (insert) → Validate (kiểm tra) → Save → [Submit → Cancel] → Trash
     │              │                    │          │
     └── hooks: before_insert, validate, on_submit, on_cancel, on_trash...
```

Ở mỗi sự kiện, lập trình viên có thể móc logic vào bằng: (a) Controller Python của chính DocType đó, (b) `doc_events` trong `hooks.py` của app, hoặc (c) Server Script cấu hình qua giao diện. Dự án dùng cách (b) rất nhiều — ví dụ `hooks.py` của `smart_helpdesk` chặn mọi `Stock Entry` submit, mọi `Sales Invoice` validate/submit/cancel để bảo vệ quy tắc riêng của SHD (giữ chỗ không bị xuất lố, hóa đơn không xuất kho hai lần…).

### 2.5. Ba khái niệm dễ nhầm quanh DocType

1. **Custom Field ≠ DocType mới.** Custom Field là *thêm một trường* vào DocType có sẵn (ví dụ thêm `custom_asset` vào `Issue`). DocType mới là *thêm một loại đối tượng hoàn toàn mới*. Chọn cái nào là quyết định kiến trúc — xem cây quyết định ở mục 5.2.
2. **Child DocType (istable=1)** chỉ sống trong bảng con của DocType cha, không có trang riêng.
3. **Single DocType** chỉ có đúng một bản ghi (kiểu trang Settings). **Virtual DocType** không có bảng thật mà đọc từ nguồn ngoài. Dự án không dùng hai loại này.

---

## PHẦN 3 — ERPNEXT CHO SẴN NHỮNG MODULE NGHIỆP VỤ GÌ?

### 3.1. Bảng tổng quan các module nghiệp vụ của ERPNext (v16)

| Nhóm module ERPNext | DocType tiêu biểu | Cho doanh nghiệp cái gì |
|---|---|---|
| **Accounting** (Kế toán) | Company, Account (hệ thống tài khoản), Journal Entry, Payment Entry, Sales Invoice, Purchase Invoice, Bank Reconciliation | Sổ cái, công nợ phải thu/phải trả, thanh toán, thuế, báo cáo tài chính |
| **Selling** (Bán hàng) | Customer, Quotation, Sales Order, Delivery Note, Price List, Item Price | Chu trình báo giá → đơn bán → giao hàng → hóa đơn phía bán |
| **Buying** (Mua hàng) | Supplier, Material Request, Request for Quotation, Purchase Order, Purchase Receipt, Purchase Invoice | Chu trình cần mua → đặt mua → nhận hàng → hóa đơn mua |
| **Stock** (Kho) | Item, Warehouse, Bin, Stock Entry, Stock Ledger Entry, Stock Reconciliation, Serial No, Batch, Item Reorder | Tồn kho theo kho, nhập/xuất/chuyển kho, định giá tồn, số serial/lô, mức đặt hàng lại |
| **Manufacturing** (Sản xuất) | BOM, Work Order *(lệnh sản xuất)*, Job Card, Production Plan | Sản xuất theo định mức — **không liên quan bảo trì hiện trường** |
| **Assets** (Tài sản) + **Maintenance** | Asset, Asset Category, Asset Maintenance, Asset Maintenance Team, Asset Maintenance Log, Asset Repair, Location | Sổ tài sản cố định **của chính công ty**: khấu hao, di chuyển, thanh lý + lịch bảo trì tài sản và nhật ký bảo trì |
| **Support** (Hỗ trợ) | Issue, Issue Type, Issue Priority, Service Level Agreement, Service Level Priority, Warranty Claim | Ticket hỗ trợ + SLA cơ bản gắn trên Issue |
| **CRM** | Lead, Opportunity, Customer, Contract, Campaign | Đầu mối, cơ hội bán hàng, hợp đồng thương mại dạng văn bản |
| **Projects** | Project, Task, Timesheet | Quản lý dự án, task, chấm công theo dự án |
| **Quality** | Quality Inspection, Quality Goal, Quality Review | Kiểm tra chất lượng hàng nhập/sản xuất |
| **Website / Portal** | Web Page, Web Form, Portal Settings | Trang web và cổng thông tin cơ bản cho khách/người dùng ngoài |
| **Frappe Core/Desk** (không phải ERPNext mà là Frappe) | User, Role, Workflow, ToDo, Assignment Rule, File, Email, Notification, Report, Workspace, Custom Field, Client Script, Server Script | Toàn bộ "khung vận hành": người dùng, phân quyền, giao việc, file, thông báo, báo cáo, công cụ tùy biến không cần code |

### 3.2. Những thứ ERPNext **không** có sẵn (nói rõ để khỏi hiểu lầm khi mapping)

- **Không có module Field Service Management (dịch vụ hiện trường) hoàn chỉnh**: không có khái niệm *lượt tác nghiệp (visit)*, *gói việc hiện trường*, *giữ chỗ vật tư cho một ca*, *nghiệm thu khôi phục bởi khách*, *callback/tái phát theo cửa sổ quan sát*… Đây là khoảng trống lớn nhất đối với bài toán AIS và là lý do app SHD tồn tại.
- **`Work Order` của ERPNext là lệnh SẢN XUẤT** (làm ra một Item theo BOM), không phải phiếu giao việc sửa chữa. Đây là cái bẫy tên gọi kinh điển: dự án bắt buộc phải đặt tên riêng `SHD Work Order`.
- **Không có HR/Payroll trong core từ v14+**: nhân sự/lương nằm ở app riêng **Frappe HR (HRMS)**, bản cài của dự án **chưa cài** app này. Vì vậy các ý tưởng trong báo cáo giữa kỳ như "quét `Leave Application` để loại KTV nghỉ phép khỏi vòng phân công" hiện **chưa có dữ liệu đầu vào thật** trên hệ thống.
- **Helpdesk hiện đại (`HD Ticket`) là app riêng Frappe Helpdesk**, bản cài của dự án không có; dự án (lớp cũ) dùng `Issue` của module Support.
- **Asset là tài sản kế toán**: tạo một `Asset` đồng nghĩa ghi nhận nguyên giá/khấu hao vào sổ của **chính công ty sở hữu**. Máy của khách đặt tại nhà máy khách không phải tài sản của AIS — dùng thẳng `Asset` cho máy khách là sai về kế toán nếu không tách bạch (quyết định kiến trúc ADR-02 trong tài liệu thiết kế của nhóm; lớp SHD chọn làm `SHD Equipment` riêng, không sinh bút toán tài sản).

### 3.3. Phân biệt 3 chữ "module" — chỗ sinh viên hay bị hỏi vặn

| Chữ "module" | Nghĩa | Ví dụ |
|---|---|---|
| Module của **ERPNext** | Nhóm DocType nghiệp vụ có sẵn | Stock, Buying, Assets, Support… |
| Module của **Frappe app** (Module Def) | Nhóm DocType thuộc về một app | App `smart_helpdesk` có 1 module `Smart Helpdesk` |
| Module **nghiệp vụ M01–M10 của dự án** | Phân rã theo chuỗi giá trị doanh nghiệp AIS do nhóm thiết kế | M05 "Kho & vật tư" dùng *cả* module Stock của ERPNext *lẫn* DocType SHD tự viết |

Khi bảo vệ đồ án, câu trả lời chuẩn là: *"M01–M10 là module nghiệp vụ theo phân tích doanh nghiệp; khi hiện thực, mỗi module nghiệp vụ ánh xạ xuống một tổ hợp gồm DocType native của ERPNext, DocType SHD tự viết và cấu hình — xem bảng mapping Phần 8."*

---

## PHẦN 4 — GIAO DIỆN: ERPNEXT CÓ CHO LUÔN HAY KHÔNG?

**Trả lời ngắn: Có, cho gần như toàn bộ giao diện quản trị.** Cụ thể:

### 4.1. Những gì có sẵn, không cần viết một dòng frontend nào

- **List View**: bảng dữ liệu có lọc, sắp xếp, phân trang, chọn nhiều dòng, xuất Excel/CSV — sinh tự động từ DocType, trường nào đặt `in_list_view` thì hiện thành cột.
- **Form View**: form chi tiết một bản ghi, tự xếp trường theo khai báo, có các tab/section, bảng con, file đính kèm, khung bình luận/giao việc (Timeline), lịch sử phiên bản.
- **Các view khác**: Report View, Kanban, Calendar, Tree (cho DocType dạng cây như Warehouse/Account), Gantt (Project/Task).
- **Workspace**: trang chủ theo vai trò, chứa shortcut, thẻ số (Number Card), biểu đồ, danh sách nhanh — cấu hình bằng kéo thả/lưu JSON.
- **Portal**: người dùng ngoài (khách hàng) đăng nhập xem phần được phép qua các trang portal/web form cơ bản.
- **Print Format**: mẫu in PDF theo chứng từ (dùng HTML/Jinja).
- Giao diện **responsive** chạy trên trình duyệt điện thoại/máy tính bảng — nhưng **không có app mobile native và không làm việc offline**.

### 4.2. Dự án này đã dùng giao diện có sẵn như thế nào?

Đây là một trong những quyết định đáng học nhất của dự án (lớp SHD):

1. **Không viết frontend riêng.** Toàn bộ nghiệp vụ chạy trong Desk tại `/desk/smart-helpdesk`.
2. **Tạo một Workspace "Smart Helpdesk"** với 10 shortcut đúng 10 module M01–M10 (khai trong `install.py` + file `smart_helpdesk/workspace/smart_helpdesk/smart_helpdesk.json`), mỗi shortcut mở danh sách DocType SHD đại diện module đó.
3. **Biến form thành "chỉ xem + thao tác bằng lệnh"**: trong `install.py`, mọi trường của 28 DocType SHD đều bị đặt `read_only = 1` và quyền DocType chỉ cho **đọc**. Người dùng **không sửa trực tiếp** trên form. Muốn làm gì (tiếp nhận, phân công, giữ vật tư, lập hóa đơn…) phải bấm nút **"Thao tác nghiệp vụ"** / **"Tạo hồ sơ"** — nút này do file JavaScript duy nhất `public/js/operations.js` (~330 dòng) gắn vào mọi form/list SHD.
4. Nút bấm đó mở **hộp thoại (Dialog) tự sinh từ danh mục lệnh server** (`api.catalog` trả về lệnh nào, tham số gì, theo đúng vai trò của người dùng), rồi gửi về **một API duy nhất**: `POST /api/method/smart_helpdesk.api.execute` kèm `command`, `payload` và `idempotency_key`. Server kiểm tra vai trò + phạm vi + trạng thái rồi mới ghi dữ liệu và trả kết quả.
5. Nhờ kiến trúc trên, giao diện **không thể** làm sai nghiệp vụ: nút nào hiện, trường nào bắt buộc đều do server quyết định; giao diện chỉ là "cái điều khiển từ xa".

Ở lớp demo cũ, giao diện cũng là Desk, nhưng tùy biến theo cách phổ thông hơn: **Client Script** gắn nút thao tác nhanh cho KTV trên form `Issue` ("Bắt đầu xử lý (Check-in)", "Xuất linh kiện sửa", "Hoàn thành ca (Resolve)") — file `scripts/setup/05_setup_quick_actions.py`.

### 4.3. Vậy có nên tự làm lại giao diện (custom UI) không?

Xem phân tích đầy đủ ở mục 6.3 — kết luận trước: **với đồ án và với giai đoạn này của dự án thì KHÔNG.** Giữ Desk, tùy biến ở mức Workspace + nút thao tác + mẫu in. Chỉ cân nhắc làm portal riêng cho khách hàng khi đi vào vận hành thật.

---

## PHẦN 5 — MUỐN BỔ SUNG MODULE THÌ LÀM SAO? MUỐN SỬA MODULE CÓ SẴN THÌ SỬA SAO?

### 5.1. Thang 6 mức can thiệp — từ nhẹ nhất đến nặng nhất

Đây là "thang kỹ sư ERP" chuẩn. **Luôn chọn mức nhẹ nhất mà vẫn đúng nghiệp vụ**, vì mức càng nặng thì càng khó nâng cấp phiên bản sau này.

| Mức | Cách làm | Khi nào dùng | Dự án đã dùng ở đâu |
|---|---|---|---|
| **1. Cấu hình thuần** | Bật/tắt tính năng, khai danh mục, đặt tham số trong các trang Settings có sẵn; tạo Role, Workflow, SLA, Assignment Rule qua giao diện | Nghiệp vụ khớp sẵn với ERPNext | Lớp cũ: 2 gói SLA VIP/Standard, Holiday List, Assignment Rule phân công KTV theo nhóm kỹ năng, Item Reorder |
| **2. Thêm trường (Custom Field)** | Thêm field vào DocType có sẵn qua giao diện hoặc code `create_custom_fields`; tiền tố `custom_` | Thiếu vài thông tin, thiếu vài mối liên kết, còn lại quy trình vẫn là của native | Lớp cũ: **19 Custom Field** (Issue 9, Stock Entry 5, Asset 4, Asset Maintenance Log 1). Lớp SHD: 5 Custom Field gắn `custom_shd_work_order` / `custom_shd_demand` lên Stock Entry, Material Request, Purchase Order, Purchase Receipt, Sales Invoice để nối chứng từ native về hồ sơ SHD |
| **3. Script nhẹ** | **Client Script** (JavaScript chạy trên form: thêm nút, ẩn/hiện trường) và **Server Script** (Python chạy theo sự kiện, trong sandbox) | Thêm tương tác nhỏ, kiểm tra phụ, tự động điền | Lớp cũ: Client Script "Issue Technician Quick Actions". Lớp SHD: cơ chế tương đương nhưng đóng vào app (Client Script được installer cài từ `operations.js`) |
| **4. Workflow & tự động hóa** | Workflow DocType, Notification, Assignment Rule, Scheduled Job | Duyệt theo trạng thái, nhắc việc, chạy việc theo lịch | Lớp SHD: scheduler daily sinh kỳ PM + lập báo cáo (`hooks.py` → `tasks.py`), nhưng chỉ chạy khi đã cấu hình user dịch vụ riêng |
| **5. Custom App (viết app Frappe riêng)** | Tạo app bằng `bench new-app`, khai DocType bằng JSON/Python, viết controller, `hooks.py` (`doc_events`, `scheduler_events`, `after_install`…), API `@frappe.whitelist()`, test, đóng gói vào repo, cài bằng `bench install-app` + `migrate` | Nghiệp vụ **khác bản chất** với native: đối tượng mới, quy tắc giao dịch mới, kiểm soát chặt | **Đây là lớp SHD**: app `smart_helpdesk` với `required_apps = ["erpnext"]`, `after_install/after_migrate = install.sync` |
| **6. Sửa thẳng mã nguồn ERPNext/Frappe** | Mở code core ra sửa | **GẦN NHƯ KHÔNG BAO GIỜ.** Mất khả năng nâng cấp, mọi bản vá bảo mật đều xung đột | Dự án **không** làm việc này — mọi tùy biến nằm trong app riêng hoặc cấu hình. Đây là điểm cộng kiến trúc rõ ràng |

### 5.2. Cây quyết định: gặp một yêu cầu mới thì chọn mức nào?

```
Yêu cầu mới đến
│
├─ ERPNext đã có sẵn tính năng, chỉ khác tên gọi/tham số? ──► Mức 1: CẤU HÌNH
├─ Chỉ thiếu vài trường thông tin / vài liên kết trên chứng từ có sẵn? ──► Mức 2: CUSTOM FIELD
├─ Thiếu một nút bấm, một kiểm tra nhỏ trên form? ──► Mức 3: CLIENT/SERVER SCRIPT
├─ Thiếu quy trình duyệt / nhắc việc / việc chạy theo lịch? ──► Mức 4: WORKFLOW / SCHEDULER
├─ Đối tượng nghiệp vụ MỚI, hoặc quy tắc giao dịch mà native không có
│   (ví dụ: giữ chỗ vật tư, work order hiện trường, snapshot quyền lợi)? ──► Mức 5: CUSTOM APP
└─ Định sửa code trong thư mục erpnext/frappe? ──► DỪNG. Tìm lại mức 1–5.
    (Ngoại lệ duy nhất: sửa xong thì gửi upstream thành đóng góp chính thức.)
```

**Ví dụ áp dụng ngay trong dự án để nhớ lâu:**
- "Ticket cần ghi thêm máy nào bị hỏng" → mức 2: Custom Field `custom_asset` trên `Issue` (lớp cũ đã làm).
- "KTV cần nút Check-in trên điện thoại" → mức 3: Client Script (lớp cũ đã làm).
- "Vật tư phải được *giữ chỗ* cho ca này, người khác không được lấy, nhưng chưa xuất kho thật" → ERPNext **không có khái niệm này** → mức 5: DocType `SHD Reservation` + logic kiểm tra đồng thời trên `Bin` (lớp SHD đã làm).
- "Máy bảo trì là máy của khách, không được hạch toán tài sản của AIS" → mức 5: `SHD Equipment` thay cho `Asset`.

### 5.3. Quy trình chuẩn khi thêm một module/nghiệp vụ mới bằng Custom App

1. **Phân tích fit–gap trước** (như Phần 8 file này): native có gì, thiếu gì, bằng chứng ở đâu.
2. `bench new-app <ten_app>` → app có khung: thư mục app, `hooks.py`, `modules.txt`, thư mục module.
3. Khai DocType: hoặc qua giao diện Desk (Developer Mode) để sinh file JSON trong app, hoặc khai bằng code như dự án này làm trong `schema.py` rồi tự tạo DocType lúc cài đặt trong `install.py` (cách này ít gặp hơn nhưng cho phép sinh schema động và khóa chặt quyền — nhóm chọn cách này có chủ đích).
4. Viết logic server (Python): controller/`doc_events`/API whitelist; **không bao giờ tin logic ở Client Script** — phía client chỉ để tiện thao tác, server phải kiểm tra lại hết (dự án làm đúng: form read-only, mọi ghi chép qua command server).
5. Gắn phân quyền: Role mới, quyền trên DocType, và nếu cần thì quyền mức bản ghi (như `SHD Access Grant` của dự án: quyền theo company/customer/site/warehouse/loại tài nguyên).
6. Viết **patch** nếu cần đổi dữ liệu cũ (`patches.txt`), **fixture** nếu cần dữ liệu cấu hình đi kèm.
7. Viết test tích hợp chạy trên site test riêng; `bench --site <site> migrate`; kiểm tra nâng cấp: cài lại/migrate lại phải không lỗi, không mất dữ liệu (installer của dự án được viết theo đúng tính chất này: "additive, repeatable" — chạy lại nhiều lần an toàn).
8. Đóng gói triển khai: bản dev có thể mount source vào container như dự án đang làm (`docker/compose.business.yml`); bản production phải **build vào image bất biến** và đi qua CI/CD (đây là yêu cầu đã ghi trong tài liệu triển khai của chính dự án, hiện chưa thực hiện).

### 5.4. Sửa module có sẵn — những điều được và không được làm

**Được (và dự án đang làm):**
- Thêm Custom Field, Custom DocPerm (quyền tùy biến), Workflow, Print Format mới.
- Móc sự kiện bằng `doc_events` trong `hooks.py` của app mình để kiểm tra/chặn/bổ sung khi chứng từ native bị thay đổi — ví dụ SHD chặn submit `Stock Entry` nếu vi phạm giữ chỗ, chặn cancel `Sales Invoice` không đúng quy trình.
- Ghi đè có kiểm soát: `override_doctype_class`, `override_whitelisted_methods` trong `hooks.py` (dự án chưa cần dùng).
- Thêm trường qua code bằng `create_custom_fields` trong hàm cài đặt (lớp SHD làm với 5 trường `custom_shd_*`).

**Không được:**
- Sửa trực tiếp DocType chuẩn rồi lưu trong giao diện mà không xuất ra app/fixture (nâng cấp sẽ mất hoặc xung đột, đồng đội không tái lập được).
- Sửa file Python/JS trong thư mục `erpnext` hay `frappe`.
- Dựa vào việc sửa dữ liệu thẳng trong MariaDB.

---

## PHẦN 6 — CÂU HỎI GIAO DIỆN, NÓI SÂU HƠN: CÓ NÊN TỰ CONFIG/VIẾT LẠI UI KHÔNG?

### 6.1. Ba lựa chọn UI trong thế giới Frappe

| Lựa chọn | Mô tả | Chi phí | Khi nào đáng |
|---|---|---|---|
| **A. Dùng Desk nguyên bản** | Form/list tự sinh, Workspace tùy biến, nút bấm bằng Client Script/Dialog | Gần như 0 | Người dùng nội bộ, nghiệp vụ chuẩn, đồ án, giai đoạn đầu vận hành |
| **B. Desk + điểm nhấn riêng** | Như A, cộng: Workspace riêng, mẫu in riêng, vài trang Page/Report tự viết trong app, portal Web Form cho khách | Thấp–trung bình | Khi cần bộ mặt theo module và khách hàng xem trạng thái cơ bản |
| **C. Frontend hoàn toàn riêng** (Vue/React/Frappe UI, gọi REST/command API) | Tự thiết kế trải nghiệm: app KTV hiện trường, portal khách hàng đẹp, dashboard riêng | Cao: phải tự lo đăng nhập, phân quyền hiển thị, kiểm thử, bảo trì theo phiên bản API | Khi có nhóm người dùng ngoài lớn, cần offline, hoặc trải nghiệm Desk thật sự cản trở công việc |

### 6.2. Dự án đang ở đâu trên thang này?

Ở **lựa chọn A, tiệm cận B**: Desk + Workspace 10 module + Dialog thao tác tự sinh + file `DESIGN.md` (bộ design system "SmartHelpDesk Modern Light": màu cobalt `#1D4ED8`, font Inter/JetBrains Mono…) — nhưng lưu ý **design system đó mới áp cho slide thuyết trình và tài liệu, chưa phải một theme Desk hoàn chỉnh**. Desk thực tế vẫn mang giao diện Frappe chuẩn.

### 6.3. Khuyến nghị của kỹ sư (cho đúng dự án này)

1. **Không viết lại UI nghiệp vụ.** Toàn bộ giá trị của dự án nằm ở tính đúng đắn của dữ liệu và quy tắc (SLA, giữ chỗ, duyệt phát sinh, đối soát). Desk đã đủ cho điều phối, thủ kho, mua hàng, kế toán và quản lý — những người dùng này làm việc trên máy tính, theo form/list.
2. **Giữ mô hình "form chỉ xem + nút lệnh" của lớp SHD.** Đây là cách lấy được UI miễn phí mà vẫn khóa được nghiệp vụ — tốt hơn hẳn mô hình lớp cũ (người dùng sửa thẳng trường trên `Issue` rồi bấm Save, rất dễ sai trạng thái).
3. **Chỗ duy nhất đáng đầu tư UI riêng sau này là phía khách hàng và KTV hiện trường**: khách cần một portal tối giản (xem ca của mình, duyệt dự toán, nghiệm thu) thay vì tài khoản Desk; KTV cần màn hình điện thoại ít thao tác. Cả hai đều gọi lại đúng 40 command API hiện có — **không phải viết lại nghiệp vụ**, đó là lý do kiến trúc command API của nhóm có giá trị lâu dài.
4. Nếu chỉ muốn "đẹp hơn cho demo/báo cáo": đầu tư vào Workspace (Number Card, biểu đồ KPI có sẵn của Frappe), Print Format cho phiếu/biên bản, và ảnh chụp hệ thống thật — đừng đầu tư vào một frontend song song.

---

## PHẦN 7 — GIẢI PHẪU CHÍNH DỰ ÁN NÀY (ĐỌC TỪ CODE, KHÔNG PHẢI TỪ SLIDE)

### 7.1. Doanh nghiệp và bài toán (AIS)

AIS bán **khả năng khôi phục thiết bị và sự dự đoán được về chi phí**, không bán "việc đóng ticket". Một ca chỉ thật sự xong khi đồng thời: máy chạy lại (kỹ thuật), khách xác nhận (nghiệm thu), vật tư/giờ công đã đối soát (thương mại) và phát sinh đã được người có thẩm quyền phía khách duyệt. Thiết kế v3 của nhóm tách bạch các khái niệm hay bị gộp sai:

- **Yêu cầu (Request) ≠ Sự cố (Incident) ≠ Gói việc (Work Order) ≠ Lượt tác nghiệp (Visit)** — một ca sửa 2 chuyến xe là 1 work order, 2 visit, không phải 2 ca.
- **Kế hoạch PM (Plan) ≠ Kỳ PM đến hạn (Occurrence)**; **Giữ chỗ (Reservation) ≠ Xuất tiêu hao (Material Use)**; **Hoàn thành kỹ thuật ≠ Nghiệm thu ≠ Đã lập hóa đơn ≠ Đã thanh toán**.

Đây là phần "tư duy ERP" giá trị nhất của đồ án — và là căn cứ để mapping ở Phần 8: ERPNext native gộp nhiều khái niệm trên vào một `Issue`/`Asset Maintenance Log`, nên không đạt yêu cầu.

### 7.2. Cấu trúc thư mục repo (đã kiểm chứng)

```
Project_SmartHelpDesk_Mainternance/
├─ apps/smart_helpdesk/            ★ CUSTOM APP (lớp nghiệp vụ mới, v3)
│  └─ smart_helpdesk/
│     ├─ schema.py                 28 DocType SHD khai bằng code + 8 Role
│     ├─ install.py                Installer: tạo Role/Module/DocType/Workspace/Client Script
│     ├─ hooks.py                  Móc sự kiện, lịch scheduler, app_js
│     ├─ api.py                    Cổng lệnh duy nhất: execute() + catalog() + master_catalog()
│     ├─ operations.py             18 command: tiếp nhận → điều phối → visit → nghiệm thu
│     ├─ maintenance.py            5 command: PM, finding, tra cứu tri thức
│     ├─ inventory.py              11 command: giữ chỗ, tiêu hao, nhu cầu mua → PO → nhận hàng
│     ├─ commercial.py             5 command: dự toán, đối soát phí, hóa đơn
│     ├─ reporting.py              1 command: snapshot KPI từ sự kiện
│     ├─ sla.py                    Engine tính hạn SLA theo lịch làm việc/timezone/ngày nghỉ
│     ├─ security.py               Quyền theo phạm vi (grant), chặn ghi trực tiếp, bảo vệ file
│     ├─ core.py                   Event journal, khóa bản ghi, kiểm tra cùng phạm vi
│     ├─ tasks.py                  Job nền: sinh kỳ PM, lập báo cáo ngày (opt-in theo user dịch vụ)
│     ├─ public/js/operations.js   UI Desk: nút "Tạo hồ sơ" / "Thao tác nghiệp vụ" + Dialog tự sinh
│     ├─ smart_helpdesk/workspace/ Workspace 10 shortcut M01–M10
│     └─ tests/                    integration.py (21 test), http_smoke.py, test_calendar.py (5 test)
├─ scripts/                        LỚP DEMO LỊCH SỬ + công cụ vận hành
│  ├─ setup/01..06_*.py            Cấu hình native qua REST: master data, KTV, custom field,
│  │                               SLA, quick actions, RBAC  (chỉ dùng cho --legacy-demo)
│  ├─ setup/install_business_app.py  Installer lớp SHD vào Docker local (có backup trước)
│  ├─ scenarios/*.py               Kịch bản demo cũ: ca sửa, mua hàng, tài chính trên Issue/Asset
│  ├─ reports/generate_kpi_dashboard.py  KPI demo cũ (đọc Issue, xuất JSON)
│  ├─ core/frappe_client.py        Client REST tối giản (chỉ dùng thư viện chuẩn Python)
│  └─ tests/run_business_checks.py Runner kiểm thử lớp SHD trên site shd-test.localhost
├─ docker/compose.business.yml     Mount app SHD vào backend/queue/scheduler của frappe_docker
├─ run_pipeline.py                 Mặc định: cài app SHD.  --legacy-demo: chạy bộ script cũ
├─ docs/
│  ├─ design/00..07_*.md           Thiết kế v3: tổng quan, yêu cầu, kiến trúc logic/dữ liệu,
│  │                               hợp đồng workflow, triển khai + 10 file modules/m01..m10
│  ├─ design/ai_architecture/      9 tài liệu AI Agent Harness + contracts/schemas (THIẾT KẾ, chưa có runtime)
│  ├─ implementation/business_modules.md  Ánh xạ thiết kế → code, hướng dẫn cài đặt/vận hành
│  ├─ reports/midterm_report.md    Báo cáo giữa kỳ (mô tả lớp demo cũ trên Issue/Asset)
│  └─ specifications/, presentation/, presentations/  Master data, ma trận kiểm chứng, slide
├─ data/*.json                     Bằng chứng kiểm thử & snapshot demo (xem 7.5)
├─ DESIGN.md                       Design system (màu/font) — áp cho slide/tài liệu
└─ output/, tmp/                   Sản phẩm build slide và file tạm
```

Ngoài repo: thư mục `E:\DUT.K1N4\HTTT\frappe_docker` (bản frappe_docker chính thức) cung cấp cụm Docker ERPNext; file `.env` / `.env.cloud` chứa khóa API để bộ script cũ gọi vào site local hoặc Frappe Cloud (hai môi trường thay thế nhau, **không đồng bộ**).

### 7.3. Kiến trúc lớp SHD — 5 ý tưởng kỹ thuật cốt lõi

1. **Schema khai bằng code, cài đặt tự sinh DocType.** `schema.py` khai 28 DocType; `install.py` (chạy ở `after_install` và `after_migrate`) tạo Role, Module Def, từng DocType (đặt `custom = 1`, `track_changes = 1`, không cho rename), các ràng buộc UNIQUE/CHECK thật trong MariaDB (ví dụ CHECK ép `SHD Work Source` đúng 1 trong 3 loại nguồn — XOR), 5 Custom Field nối chứng từ native, và Client Script cho mọi DocType. Chạy lại installer/migrate là an toàn (cộng thêm, không phá dữ liệu).
2. **Mọi ghi chép đi qua Command API.** Form Desk bị khóa read-only; quyền DocType chỉ cho đọc. Mọi thay đổi gọi `smart_helpdesk.api.execute(command, payload, idempotency_key)`:
   - Kiểm tra **role** được phép chạy lệnh đó (khai bằng decorator `@command(...)` ngay trên hàm nghiệp vụ, Service Manager luôn có quyền).
   - Kiểm tra **phạm vi** (grant theo company/customer/site/warehouse/loại tài nguyên) và **thẩm quyền** phía khách (`SHD Contact Authority`: quyền Accept / Approve Cost, có hạn mức và thời hạn).
   - **Idempotency**: mỗi lệnh ghi một bản ghi `SHD Command` với khóa băm (actor+command+key) và `binding_hash` của nội dung. Gửi lại cùng key + cùng nội dung → trả kết quả cũ; cùng key + nội dung khác → lỗi `IDEMPOTENCY_CONFLICT`; deadlock → rollback toàn bộ và báo `CONCURRENCY_CONFLICT`, thử lại bằng chính key đó.
3. **Event journal làm nguồn sự thật cho báo cáo.** Mọi thay đổi trên hồ sơ SHD đều sinh một `SHD Event` (loại sự kiện, đối tượng, phiên bản, thời điểm xảy ra/ghi nhận, người thực hiện, `command_id`, toàn bộ payload) **trong cùng transaction** với thay đổi đó. KPI (M08) không đọc trạng thái hiện tại mà **dựng lại sự thật tại thời điểm `as_of`** từ event — nên báo cáo có thể sửa lại kỳ cũ bằng snapshot mới (`supersedes`), ghi rõ tử số/mẫu số/dữ liệu thiếu thay vì bịa tỉ lệ 100%.
4. **SLA là engine riêng, không dùng SLA native.** `sla.py` tính hạn phản hồi/khôi phục từ **policy nằm trong chính hợp đồng** (`SHD Agreement.policy` dạng JSON: mốc neo `reported_at` hoặc `received_at`, `timezone`, lịch tuần theo ca làm việc, ngày nghỉ lễ, số phút phản hồi/khôi phục). Đồng hồ **không tạm dừng** ở P1 (`pause_policy = "No pause"`) — khoảng chờ vẫn được ghi bằng `SHD Wait Interval` để phân tích, nhưng không giấu thời gian đã trôi. Đây là lựa chọn có chủ đích, khác với cách SLA native của ERPNext tính từ `creation` của Issue.
5. **Chứng từ tiền/kho vẫn là chứng từ native.** Tiêu hao vật tư sinh `Stock Entry` thật (có sổ `Stock Ledger Entry`), mua hàng đi MR → PO → Purchase Receipt native, hóa đơn là `Sales Invoice` native với `update_stock = 0` (tránh xuất kho lần hai). Hooks chặn các đường đi tắt: không submit Stock Entry vi phạm giữ chỗ, không sửa/hủy Sales Invoice ngoài quy trình, file đính kèm bị kiểm tra quyền. Giá vốn (permlevel 1, chỉ Manager/Kế toán thấy) tách khỏi giá bán.

### 7.4. 28 DocType SHD và 40 command — bản đồ đầy đủ

**28 DocType** (mọi DocType đều có sẵn các trường chung: `company`, `customer`, `site`, `status`, `revision`, `details`):

| Nhóm | DocType | Vai trò |
|---|---|---|
| Nền & phạm vi | `SHD Site`, `SHD Equipment`, `SHD Agreement`, `SHD Entitlement` | Địa điểm nhà máy; hồ sơ máy kỹ thuật (không phải tài sản kế toán); hợp đồng có phiên bản + policy SLA; snapshot quyền lợi tại thời điểm áp dụng |
| Kiểm soát | `SHD Access Grant`, `SHD Contact Authority`, `SHD Technician` | Cấp quyền theo phạm vi/tài nguyên/kho; thẩm quyền người phía khách (nghiệm thu / duyệt phí, hạn mức, hiệu lực); hồ sơ KTV (kỹ năng, cửa sổ khả dụng) |
| Vận hành ca | `SHD Request`, `SHD Incident`, `SHD Work Source`, `SHD Work Order`, `SHD Visit`, `SHD Time Log`, `SHD Acceptance`, `SHD Wait Interval` | Yêu cầu; sự cố; nguồn việc (XOR 3 loại); gói việc; lượt tác nghiệp; giờ công; nghiệm thu của khách; khoảng chờ có lý do/ETA |
| Bảo trì định kỳ | `SHD PM Plan`, `SHD PM Occurrence`, `SHD Finding` | Kế hoạch PM + checklist theo phiên bản; kỳ đến hạn (giữ hạn gốc khi hoãn); bất thường phát hiện khi PM |
| Kho & mua | `SHD Reservation`, `SHD Material Use`, `SHD Compatibility`, `SHD Demand` | Giữ chỗ vật tư; tiêu hao thật tại visit; tương thích model máy ↔ vật tư; nhu cầu mua gắn nguồn work order |
| Thương mại | `SHD Estimate`, `SHD Charge` | Dự toán phát sinh có hash nội dung + hạn hiệu lực + khách duyệt; khoản phí theo nguồn (vật tư/giờ công) với chính sách Warranty/Billable/Goodwill |
| Tri thức & đo lường | `SHD Knowledge`, `SHD KPI Snapshot` | SOP/bài học theo model + phiên bản + người duyệt + hiệu lực (không dùng LLM); snapshot KPI bất biến theo kỳ |
| Nhật ký hệ thống | `SHD Event`, `SHD Command` | Sổ sự kiện nghiệp vụ; biên nhận lệnh (idempotency/audit) — người dùng thường không thao tác trực tiếp |

**40 business command** theo file: `operations.py` 18 (register, activate, revoke, receive_request, triage, acknowledge, create_work_order, assign, start_visit, finish_visit, log_time, restore, accept_work, close_request, wait, end_wait, classify_callback, correct_restoration) · `inventory.py` 11 (declare_materials, available_stock, reserve, release_reservation, consume, transfer_reserved, create_demand, requisition, prepare_purchase_order, approve_purchase_order, receive_purchase) · `maintenance.py` 5 (generate_pm, postpone_pm, complete_pm, classify_finding, search_knowledge) · `commercial.py` 5 (propose_estimate, decide_estimate, reconcile_charge, prepare_invoice, cancel_service_invoice) · `reporting.py` 1 (snapshot_kpis).

**8 Role riêng của AIS:** AIS Service Manager, AIS Dispatcher, AIS Field Technician, AIS Warehouse Keeper, AIS Purchasing, AIS Billing Accountant, AIS Customer Portal, AIS Knowledge Reviewer. (Lưu ý vai trò khách `AIS Customer Portal` bị đặt `desk_access = 0` ở lớp cũ; ở lớp SHD, phía khách mới có API kiểm quyền, **chưa có portal riêng** — xem Phần 9.)

### 7.5. Bằng chứng kiểm thử — cái gì đã được chứng minh, cái gì chưa

| Bằng chứng | Nội dung | Mức tin cậy |
|---|---|---|
| `data/business_validation.json` (15/10/2026) | Site test `shd-test.localhost`, Frappe 16.33.1 / ERPNext 16.34.2 / MariaDB 11.8: **21 test tích hợp pass**, test tranh chấp giữ chỗ 2 kết nối song song (1 Held, 1 bị từ chối đúng thiết kế), test HTTP có đăng nhập (gửi lại cùng key không trùng, đổi nội dung bị conflict, GET không ghi được, Guest bị chặn), **5 test lịch SLA pass** | Bằng chứng runtime thật cho lớp SHD |
| `apps/smart_helpdesk/smart_helpdesk/tests/` | `integration.py` 21 ca (test_01→21: từ retry/conflict, PM/finding, scope/file/ghi trực tiếp bị chặn, đến scheduler và quyền xem giá vốn), `test_calendar.py` 5 ca, `http_smoke.py` | Mã kiểm thử có trong repo |
| `data/business_ui_validation.json` | Workspace render được, list có nút thao tác, dialog lệnh mở được, 0 lỗi console sau khi sửa proxy/nginx | Bằng chứng UI Desk lớp SHD |
| `data/verification_evidence.json`, `procurement_evidence.json`, `finance_evidence.json`, `kpi_dashboard.json` | Snapshot của **lớp demo cũ** (Issue/Asset): 3 khách, 5 máy, 12 vật tư, ca warranty/billable/goodwill… | Chỉ là dữ liệu demo lịch sử — **không** dùng làm bằng chứng cho lớp SHD, và chính README của dự án cũng ghi rõ điều này |
| `docs/design/ai_architecture/contracts/conformance_results.json` | Kiểm tra offline các schema/contract của thiết kế AI | Không phải bằng chứng AI chạy thật — **chưa có runtime AI nào cả** |

Trạng thái Git cần biết khi bảo vệ/quản lý dự án: tại thời điểm đọc (28/10/2026), thư mục **`apps/` (toàn bộ lớp SHD), `docker/compose.business.yml`, `docs/implementation/` đang ở trạng thái chưa commit (`??`)** trên máy Bao; các commit đã push chủ yếu là tài liệu/slide. Việc cần làm ngay về quản trị: commit và push lớp SHD, nếu không toàn bộ phần code quan trọng nhất chỉ tồn tại trên một máy.

---

## PHẦN 8 — MAPPING CHUẨN: M01–M10 ↔ ERPNEXT NATIVE ↔ DỰ ÁN ĐÃ LÀM GÌ ↔ CÒN THIẾU GÌ

### 8.0. Cách đọc bảng và thang mức độ

- **FIT** — ERPNext có sẵn, dùng thẳng (chỉ cấu hình).
- **FIT+** — Có sẵn là chính, cần cấu hình/Custom Field/script nhẹ.
- **GAP–SỬA** — Có sẵn một phần nhưng thiếu bản chất; phải bổ sung DocType/logic mới *cạnh* native (không sửa core).
- **GAP–MỚI** — ERPNext không có; phải làm mới hoàn toàn trong custom app.
- **CHƯA LÀM** — Thiết kế đã có nhưng đợt triển khai hiện tại chưa hiện thực (theo chính tài liệu dự án).

### 8.1. Bảng mapping tổng hợp

| Module dự án | ERPNext native tương ứng | Lớp demo cũ (giữa kỳ) đã dùng | Lớp SHD hiện tại | Kết luận | Việc còn lại chính |
|---|---|---|---|---|---|
| **M01** Khách hàng & hợp đồng | Customer, Contact, Address, Contract (CRM), Service Level Agreement | Customer + 2 gói SLA VIP/Standard gắn trên Issue | Customer native + `SHD Site`, `SHD Agreement` (phiên bản + policy JSON), `SHD Entitlement` (snapshot), `SHD Contact Authority` | **GAP–MỚI** cho hợp đồng dịch vụ theo phiên bản/snapshot; FIT cho danh mục khách | Chốt chính sách hợp đồng thật bằng khảo sát; chưa có quản lý nhiều hợp đồng phức tạp cho một ca |
| **M02** Tiếp nhận & SLA | Issue, Issue Type/Priority, Service Level Agreement | Issue + Custom Field `custom_incident_time`, `custom_asset`… + SLA native | `SHD Request`, `SHD Incident`, `SHD Wait Interval` + engine `sla.py` riêng theo policy của hợp đồng | **GAP–MỚI** (native tính SLA từ lúc tạo Issue, không có reported/received riêng, không snapshot quyền lợi) | Chưa có SLA pause, escalation/thông báo tự động, kênh hotline/Zalo tích hợp |
| **M03** Điều phối & tác nghiệp | ToDo, Assignment Rule (chỉ gán việc, không phải work order hiện trường); *Work Order = sản xuất* | Assignment Rule round-robin theo nhóm kỹ năng + Client Script quick actions trên Issue | `SHD Work Source` (XOR), `SHD Work Order`, `SHD Technician`, `SHD Visit`, `SHD Time Log`, `SHD Acceptance` + 18 command operations | **GAP–MỚI** — đây là module tự xây nhiều nhất, đúng bản chất FSM | Chưa tối ưu lịch/tuyến; chưa tích hợp nghỉ phép (không có HRMS); phân công vẫn do điều phối quyết định, hệ thống kiểm tra kỹ năng/khả dụng/trùng lịch |
| **M04** Thiết bị & bảo trì định kỳ | Asset, Asset Maintenance, Asset Maintenance Log, Asset Category, Location | Asset + Asset Maintenance/Log cho cả máy khách | `SHD Equipment`, `SHD PM Plan`, `SHD PM Occurrence`, `SHD Finding` | **GAP–MỚI** cho máy khách (tránh hạch toán tài sản); FIT nếu là tài sản nội bộ của AIS | Chưa có lịch sử di chuyển máy (location event), serial/batch/core-return trong lớp SHD; quyết định ranh giới Asset↔Equipment cần chốt với kế toán khi vận hành thật |
| **M05** Kho & vật tư | Item, Warehouse, Bin, Stock Entry, Stock Ledger Entry, Item Reorder | Stock Entry (Transfer/Issue), kho xe KTV, reorder level | Native giữ nguyên cho sổ kho + `SHD Reservation`, `SHD Material Use`, `SHD Compatibility` + hooks bảo vệ Bin/Stock Entry | **FIT+ cho sổ kho; GAP–MỚI cho giữ chỗ/tương thích** — mẫu hình "native làm sổ, app làm quy tắc" chuẩn nhất dự án | Chưa hỗ trợ serial/batch và thu hồi linh kiện cũ (core recovery) trong lớp SHD |
| **M06** Mua hàng & bổ sung | Material Request, Purchase Order, Purchase Receipt, Supplier | Luồng MR→PO→PR + chuyển kho xe chạy demo end-to-end | `SHD Demand` gắn nguồn work order + MR/PO/PR native + duyệt PO theo `binding_hash` + nhận một phần/hàng reject vào kho cách ly | **FIT+ / GAP–SỬA nhẹ**: quy trình native đủ, app thêm chống mua trùng theo nguồn và duyệt đúng nội dung | Chưa gộp nhiều demand vào một PO, chưa phân bổ một PO cho nhiều ca, chưa chính sách ngoại tệ |
| **M07** Chi phí & hóa đơn | Sales Invoice, Price List, Payment Entry, Account | 3 ca demo warranty / billable / goodwill trên Issue + Sales Invoice | `SHD Estimate` (phiên bản + hash + hạn + khách duyệt), `SHD Charge` (theo nguồn, tách giá vốn/giá bán), Sales Invoice native (`update_stock = 0`), hủy hóa đơn có quy trình riêng | **GAP–SỬA**: hóa đơn dùng native, nhưng dự toán được duyệt và đối soát theo nguồn là làm mới | Chưa có credit note/điều chỉnh phức tạp, một charge chia nhiều hóa đơn; thanh toán/công nợ dùng native nhưng chưa nối quy trình thu tiền vào luồng ca |
| **M08** Báo cáo & KPI | Report Builder, Dashboard, Number Card | Script Python đọc Issue, xuất `kpi_dashboard.json` (tỉ lệ có phần gán cứng trong demo) | `SHD Event` journal + `SHD KPI Snapshot` bất biến: SLA response/restoration, PM theo hạn gốc, FTFR có cửa sổ callback, tài chính theo cohort ca — luôn kèm tử/mẫu/số thiếu | **GAP–MỚI** về phương pháp đo (native không có event-sourced KPI cho nghiệp vụ này) | Chưa có dashboard trực quan hoàn chỉnh trong Desk cho quản lý; báo cáo là snapshot theo lệnh/scheduler, chưa có escalation tự động từ KPI |
| **M09** Tri thức & trợ lý AI | File, (không có knowledge base nghiệp vụ; Helpdesk app riêng có bài viết hỗ trợ nhưng không cài) | Chưa làm ở giữa kỳ (mới định hướng RAG trong báo cáo) | `SHD Knowledge`: catalog SOP/bài học theo model, phiên bản, người duyệt, hiệu lực + lệnh `search_knowledge` theo từ khóa và quyền. **AI/RAG: mới có 9 tài liệu thiết kế + contracts/schemas + kiểm tra offline** | **GAP–MỚI một nửa**: catalog tri thức = đã làm; **AI runtime = CHƯA LÀM** (hoãn có chủ đích) | LLM, embedding/vector DB, ingestion, agent orchestrator, checkpoint/HITL chạy thật — tất cả chưa có code runtime |
| **M10** Quản trị & kiểm soát | User, Role, User Permission, Custom DocPerm, File, Version | Role AIS + User Permission + Custom DocPerm trên Issue/Stock Entry… | 8 Role AIS + `SHD Access Grant` theo company/customer/site/resource/warehouse + `SHD Contact Authority` + chặn ghi trực tiếp toàn bộ DocType SHD + bảo vệ File + `SHD Command`/`SHD Event` journal | **GAP–SỬA**: khung quyền native là nền, nhưng quyền theo phạm vi nghiệp vụ và "chỉ ghi qua command" là kiến trúc riêng của dự án | Chưa có duyệt nhiều cấp/ủy quyền (delegation), chưa diễn tập backup/restore & HA, quyền của lớp dữ liệu cũ (Issue…) cần audit/migration riêng |

### 8.2. Đọc sâu từng module (vì sao kết luận như vậy)

**M01 — Khách hàng & hợp đồng.** ERPNext có `Customer` rất tốt cho danh mục và công nợ, nên dự án giữ nguyên. Nhưng một *hợp đồng dịch vụ bảo trì* trong bài toán AIS không phải văn bản `Contract` của CRM: nó phải trả lời được "máy nào, ở site nào, được hưởng dịch vụ gì, phản hồi trong bao lâu, theo lịch làm việc nào, ai phía khách được duyệt gì" — và câu trả lời phải được **đóng băng tại thời điểm tiếp nhận ca** (entitlement snapshot), vì hợp đồng sửa sau không được làm thay đổi quyền lợi của ca đã nhận. Native không có cấu trúc này → `SHD Agreement` (policy dạng JSON có validate chặt) + `SHD Entitlement` là làm mới đúng chỗ.

**M02 — Tiếp nhận & SLA.** Đây là chỗ sinh viên hay bị hỏi nhất: "ERPNext có Issue + SLA rồi, sao phải làm mới?" Trả lời bằng 4 khác biệt đo được: (1) SLA native neo vào thời điểm **tạo bản ghi** (`creation`), trong khi thực tế khách báo qua hotline lúc 08:00, điều phối nhập hệ thống lúc 08:20 — dự án tách `reported_at` / `received_at` / `recorded_at` và cho policy chọn mốc neo; (2) hạn SLA phải tính theo **lịch làm việc của hợp đồng** (ca sáng/chiều, nghỉ trưa, lễ, timezone), không phải cộng thẳng số phút — `sla.py` làm đúng việc này và có 5 test lịch; (3) một sự cố có thể có **nhiều yêu cầu** báo về (trùng) và một yêu cầu có thể không phải sự cố — native gộp tất cả vào một Issue; (4) khoảng chờ khách/vật tư phải được ghi lại mà **không được xóa thời gian SLA đã trôi** — native không có `Wait Interval` như một đối tượng riêng.

**M03 — Điều phối & tác nghiệp.** Native chỉ có `Assignment Rule` (tự gán một DocType cho user theo round-robin/load-balancing) và `ToDo` (việc được giao). Cả hai đều không phải *work order hiện trường*: không có gói việc sinh từ đúng một nguồn (sự cố / yêu cầu tư vấn / kỳ PM — ràng buộc XOR có CHECK trong DB), không có nhiều lượt tác nghiệp với giờ giấc và bằng chứng riêng, không có thử máy khôi phục và nghiệm thu của khách như các sự kiện riêng. Vì vậy M03 là module tự xây nặng nhất (6 DocType, phần lớn trong 18 command của `operations.py`) — và đó là quyết định đúng, vì đây là lõi FSM của đề tài.

**M04 — Thiết bị & PM.** Lớp cũ dùng `Asset` + `Asset Maintenance` chạy được demo, nhưng mang theo hệ quả kế toán sai khi máy là của khách. Lớp SHD tách `SHD Equipment` (hồ sơ kỹ thuật thuần: mã máy, model, serial, mức criticality, cấu hình) khỏi tài sản kế toán. PM cũng được tách đúng bản chất: `Plan` (có checklist theo phiên bản) sinh `Occurrence` theo kỳ (`period_key` chống sinh trùng, hoãn vẫn **giữ hạn gốc** để đo đúng hạn), `Finding` là đối tượng có chủ trách nhiệm và hạn xử lý riêng — hoàn thành PM **không** tự đóng finding. Native `Asset Maintenance Log` gộp các khái niệm này vào một nhật ký, không đạt.

**M05 — Kho & vật tư.** Ngược lại với M03, đây là nơi **không được viết lại**: sổ kho của ERPNext (`Bin` = tồn hiện tại, `Stock Ledger Entry` = sổ cái kho bất biến, `Stock Entry` = chứng từ nhập/xuất/chuyển) đã chuẩn. Cái native thiếu là lớp *cam kết*: vật tư đã **giữ cho ca này** thì ca khác không được hứa nữa, dù hàng vẫn nằm trong kho. `SHD Reservation` cộng với kiểm tra `tồn khả dụng = Bin thực tế − tổng đang giữ` trong cùng transaction (và test tranh chấp 2 kết nối đã chứng minh không giữ lố được) là phần làm mới tối thiểu và đúng chỗ. Tiêu hao tại visit mới sinh Stock Entry thật — giữ chỗ không làm thay đổi sổ kho.

**M06 — Mua hàng.** Chuỗi MR → PO → PR của native đủ chuẩn (có trạng thái, có liên kết dòng, có nhận một phần). App chỉ thêm 3 thứ native thiếu theo nguồn gốc: nhu cầu mua **bắt buộc sinh từ work order** (`SHD Demand`) nên không mua trùng/mua không căn cứ; PO được **duyệt theo đúng nội dung** (`binding_hash` — sửa PO sau khi duyệt là bị phát hiện); hàng reject đi vào **kho cách ly** chứ không nhập thành hàng dùng được. Đây là mẫu "GAP–SỬA" điển hình: 80% native, 20% quy tắc riêng.

**M07 — Chi phí & hóa đơn.** `Sales Invoice` native lo hạch toán, thuế, công nợ — giữ nguyên. Hai thứ phải làm mới: (1) **dự toán phát sinh được khách duyệt trước khi làm** — `SHD Estimate` có dòng chi tiết, tổng tiền, `binding_hash`, hạn hiệu lực; thay dự toán thì bản cũ mất hiệu lực và phải duyệt lại (có test riêng); quyền duyệt kiểm tra qua `SHD Contact Authority` (đúng người, đúng hạn mức, còn hiệu lực). (2) **khoản phí phải truy được về nguồn** — `SHD Charge` chỉ sinh từ `SHD Material Use` hoặc `SHD Time Log` đã xác nhận, mang chính sách Warranty/Billable/Goodwill; giá vốn giờ công/vật tư là trường permlevel 1 mà KTV không nhìn thấy. Hóa đơn lập từ charge đã đối soát và đặt `update_stock = 0` vì vật tư đã xuất ở bước tiêu hao — tránh lỗi trừ kho hai lần kinh điển.

**M08 — Báo cáo & KPI.** Điểm yếu của lớp cũ là dashboard JSON với một số tỉ lệ "đẹp" do dữ liệu demo ít và cách tính đơn giản. Lớp SHD đổi phương pháp: KPI được tính từ **event journal** tại một thời điểm chốt (`as_of`/`watermark`), mỗi chỉ số trả về tử số, mẫu số và số bản ghi thiếu mốc (ví dụ ca chưa có `restoration_due` thì tính vào `missing`, không lặng lẽ loại ra); FTFR (sửa đúng ngay lần đầu) chỉ tính khi cửa sổ callback đã đóng; PM tính theo **hạn gốc** kể cả đã hoãn. Snapshot là bất biến — số liệu kỳ cũ bị sự kiện đến muộn làm thay đổi thì sinh snapshot mới nối `supersedes`, không sửa đè. Đây là cách làm báo cáo "kiểm toán được" mà Report Builder native không tự cho.

**M09 — Tri thức & AI.** Phải tách hai nửa khi trình bày: *catalog tri thức* (SOP, bài học từ ca — theo model máy, phiên bản tài liệu, người duyệt, thời gian hiệu lực, tìm kiếm theo từ khóa có kiểm quyền) **đã làm** trong `SHD Knowledge`. *Trợ lý AI/Agent Harness* (RAG, vector DB, orchestrator, checkpoint, human-in-the-loop) mới dừng ở **bộ thiết kế 9 tài liệu + JSON Schema contracts + bộ kiểm tra conformance offline** trong `docs/design/ai_architecture/` — theo quyết định của chính dự án là **hoãn**, và pyproject của app còn ghi rõ mô tả: *"AIS service operations for ERPNext; no AI runtime"*. Nói "đã tích hợp AI" khi bảo vệ là sai sự thật; nói đúng là "đã thiết kế kiến trúc AI và kiểm chứng contract ở mức offline; runtime chưa triển khai".

**M10 — Quản trị & kiểm soát.** Nền native (User/Role/Permission) là cần nhưng chưa đủ cho bài toán nhiều khách: một KTV thuộc AIS không có nghĩa được xem mọi khách, mọi kho, mọi giá vốn. Lớp SHD thêm tầng quyền nghiệp vụ: `SHD Access Grant` theo (company, customer, site, loại tài nguyên, warehouse, hành động read/operate, hạn hiệu lực), áp ở **mọi đường vào** — Desk list, form, REST, file đính kèm, scheduler và cả việc đọc lại biên nhận lệnh cũ. Cộng với nguyên tắc "form read-only, chỉ ghi qua command" và journal `SHD Event`/`SHD Command`, M10 trở thành lớp kiểm soát ngang thật sự, không chỉ là ma trận role trên giấy như lớp cũ.

### 8.3. Bảng mapping theo DocType native (tra nhanh khi bị hỏi "cái X dùng cái gì?")

| Nhu cầu | DocType native | Cách dự án dùng | Trạng thái |
|---|---|---|---|
| Khách hàng / nhà cung cấp / công ty | Customer / Supplier / Company | Dùng thẳng làm master data | FIT |
| Vật tư, kho, tồn, sổ kho | Item / Warehouse / Bin / Stock Entry / Stock Ledger Entry | Dùng thẳng; SHD móc hook bảo vệ | FIT |
| Cần mua → đặt mua → nhận hàng | Material Request / Purchase Order / Purchase Receipt | Dùng thẳng + `SHD Demand` + trường nối `custom_shd_demand` | FIT+ |
| Hóa đơn bán, bảng giá | Sales Invoice / Price List | Dùng thẳng + `SHD Estimate`/`SHD Charge` ở trước + `custom_shd_work_order` | FIT+ |
| Ticket hỗ trợ | Issue | **Lớp cũ dùng; lớp SHD thay bằng `SHD Request`/`SHD Incident`** | ĐÃ THAY THẾ (dữ liệu cũ chưa migrate) |
| SLA trên ticket | Service Level Agreement | **Lớp cũ dùng; lớp SHD thay bằng policy trong `SHD Agreement` + `sla.py`** | ĐÃ THAY THẾ |
| Tài sản & lịch bảo trì | Asset / Asset Maintenance / Asset Maintenance Log | **Lớp cũ dùng; lớp SHD thay bằng `SHD Equipment`/`SHD PM *`** cho máy khách | ĐÃ THAY THẾ (máy khách) |
| Giao việc tự động | Assignment Rule / ToDo | Lớp cũ dùng round-robin theo kỹ năng; lớp SHD: điều phối ra lệnh `assign`, hệ thống kiểm tra | THAY ĐỔI MÔ HÌNH |
| Field service work order | — (Work Order native là sản xuất) | `SHD Work Order` + `SHD Visit` tự xây | GAP–MỚI |
| Giữ chỗ vật tư | — | `SHD Reservation` tự xây trên Bin native | GAP–MỚI |
| Nhân sự / nghỉ phép | — (ở app HRMS riêng) | **Chưa cài HRMS**; khả dụng KTV khai trong `SHD Technician` | CHƯA CÓ |
| Helpdesk hiện đại | — (ở app Frappe Helpdesk riêng) | **Chưa cài**; dùng Desk + Workspace SHD | CHƯA CÓ |
| Sản xuất, chất lượng, dự án, POS, website bán hàng | Manufacturing / Quality / Projects / POS / Website | Không liên quan bài toán AIS | KHÔNG DÙNG (đúng) |

### 8.4. Những hiểu lầm cần tránh khi trình bày dự án

1. **"Dự án dùng module Support của ERPNext"** — chỉ đúng với bản giữa kỳ. Bản hiện tại dùng Support *rất ít* (gần như không), lõi ca nằm ở SHD.
2. **"Đã có AI/RAG"** — chưa. Mới có thiết kế + conformance offline (xem M09).
3. **"Đã có portal cho khách"** — chưa. Role khách và API kiểm quyền đã có; giao diện portal riêng chưa làm.
4. **"Đã triển khai production"** — chưa. Hiện chạy Docker local (frappe_docker `pwd.yml` vốn là cấu hình demo của chính frappe_docker) với cơ chế mount source; tài liệu triển khai mục tiêu (07) mô tả kiến trúc production đích (nhiều node, image bất biến, CI/CD, backup/HA) nhưng đó là **thiết kế**, chưa phải hệ thống đang chạy.
5. **"Số liệu KPI 100% chứng minh hệ thống tốt"** — các JSON demo cũ là dữ liệu mẫu ít ca; lớp SHD cố tình thiết kế để không thể kết luận như vậy (tử/mẫu/thiếu phải đi cùng nhau).

---

## PHẦN 9 — DANH SÁCH "CHƯA CÓ" ĐẦY ĐỦ (GAP LIST ĐỂ LÊN KẾ HOẠCH)

Theo tài liệu triển khai của chính dự án (`docs/implementation/business_modules.md`, mục "Phần ngoài đợt triển khai") đối chiếu với code đã đọc:

**Chưa có trong hệ thống (cả native lẫn SHD):**
1. Portal chuyên biệt cho khách hàng (xem ca, duyệt dự toán, nghiệm thu trên giao diện riêng) và thông báo/escalation tự động (email/Zalo/hotline tích hợp).
2. SLA pause có điều kiện (hiện đồng hồ chạy liên tục; khoảng chờ chỉ để ghi nhận/phân tích).
3. Ứng dụng mobile / làm việc offline cho KTV; tích hợp IoT và bảo trì dự đoán.
4. Runtime AI: LLM, RAG/ingestion/vector DB, agent orchestrator, checkpoint/resume, human-in-the-loop chạy thật.
5. Duyệt nhiều cấp và ủy quyền (delegation) phê duyệt; tối ưu hóa lịch/tuyến đường cho nhiều KTV.
6. Các nhánh nghiệp vụ nâng cao ở P1 bị chặn có chủ đích: sửa phạm vi việc đã thực hiện/nghiệm thu, chuyển máy giữa các site, serial/batch tracking và thu hồi linh kiện cũ (core recovery) trong lớp SHD, credit note, một khoản phí chia cho nhiều hóa đơn, gộp nhiều demand vào một PO.
7. Đóng kỳ báo cáo tự động và gửi cảnh báo từ KPI (scheduler mới sinh snapshot, chưa chốt kỳ/chưa gửi escalation).

**Đã có ở lớp cũ nhưng chưa migrate sang lớp SHD:**
8. Toàn bộ dữ liệu demo trên `Issue`/`Asset` (5 máy, các ca ISS-2026-…) và bộ quyền cấu hình trên DocType native — cần audit và kế hoạch migration riêng nếu muốn giữ làm dữ liệu trình bày thống nhất.
9. Các tiện ích lớp cũ: Assignment Rule theo kỹ năng, quick actions trên Issue, Item Reorder tự động — lớp SHD thay bằng mô hình khác (điều phối chủ động + kiểm tra server), không phải "mất tính năng" nhưng phải giải thích được khi bị hỏi.

**Việc kỹ thuật/quản trị còn tồn:**
10. Commit + push toàn bộ lớp SHD lên GitHub (hiện còn là file chưa commit trên máy cá nhân).
11. Đóng gói production: build image chứa app thay vì mount source, quy trình CI/CD, diễn tập backup/restore, cấu hình HTTPS/domain thật.
12. Cấu hình vận hành thật trước khi dùng: user dịch vụ cho scheduler (`shd_scheduler_user`, `shd_report_user`, `shd_report_lookback_days`), chính sách SLA/hợp đồng lấy từ khảo sát thật thay vì số demo, phân quyền grant cho từng người dùng thật.
13. UAT với người dùng nghiệp vụ, kiểm thử tải và đánh giá bảo mật độc lập (bộ test hiện tại là kiểm thử tích hợp của nhóm, không phải chứng nhận).

---

## PHẦN 10 — LỘ TRÌNH NÂNG CẤP ĐỀ XUẤT (THEO THỨ TỰ KỸ SƯ SẼ LÀM)

| Giai đoạn | Việc | Vì sao làm trước/sau |
|---|---|---|
| **0. Chốt quản trị** | Commit/push lớp SHD; đóng băng phiên bản Frappe/ERPNext v16 đang dùng; viết rõ ranh giới hai lớp trong README | Mất code là rủi ro lớn nhất hiện tại, lớn hơn mọi thiếu tính năng |
| **1. Thống nhất một lớp** | Quyết định lớp SHD là hệ thống chính thức; hoặc migrate dữ liệu demo Issue→SHD Request, hoặc ghi rõ dữ liệu cũ chỉ là tư liệu giữa kỳ | Tránh tình trạng "hai hệ thống song song, không biết tin cái nào" |
| **2. Hoàn thiện vận hành lõi** | Cấu hình user dịch vụ + scheduler; bộ dữ liệu cấu hình thật (hợp đồng/policy/kho/khách); diễn tập backup/restore trên site test | Có những thứ code đã hỗ trợ nhưng chưa bật — rẻ nhất, giá trị ngay |
| **3. Mặt tiền người dùng** | Portal khách tối giản gọi lại command API (xem ca/duyệt dự toán/nghiệm thu); thông báo email theo sự kiện SLA | Người dùng ngoài là khoảng trống trải nghiệm lớn nhất; API đã sẵn nên không đụng lõi |
| **4. Mở rộng nghiệp vụ P2** | SLA pause có điều kiện, duyệt nhiều cấp/ủy quyền, serial/batch + core return, gộp demand→PO | Làm sau khi lõi vận hành ổn định và có dữ liệu thật để kiểm chứng quy tắc |
| **5. AI sau cùng** | Triển khai M09 runtime theo đúng bộ thiết kế đã có: ingestion → hybrid retrieval → single orchestrator → HITL, có evaluation trước pilot | AI đứng trên dữ liệu tri thức và quy trình đã chuẩn; làm sớm hơn chỉ tạo demo mong manh |

Nguyên tắc xuyên suốt: **mỗi bước đều đi qua thang mức 1→5 ở Phần 5** — cấu hình trước, custom app sau; không sửa core; mọi logic quan trọng phải nằm ở server và có test.

---

## PHẦN 11 — TỰ KIỂM TRA / CÂU HỎI VẤN ĐÁP THƯỜNG GẶP

1. **Frappe và ERPNext khác nhau thế nào?** — Frappe là framework (DocType, Desk, quyền, workflow, API, scheduler); ERPNext là app nghiệp vụ chạy trên Frappe. Dự án cài thêm app thứ ba `smart_helpdesk` vào cùng site.
2. **DocType là gì?** — Khai báo metadata của một loại đối tượng; từ một khai báo, Frappe sinh bảng `tab<Tên>`, form, list, API và chỗ gắn quyền/workflow. "DocType cũng là một DocType" vì định nghĩa của nó tự lưu thành bản ghi trong `tabDocType`.
3. **ERPNext có sẵn giao diện không?** — Có, Desk sinh tự động theo DocType. Dự án chỉ thêm Workspace, nút thao tác và Dialog — không viết frontend riêng.
4. **Vì sao không dùng Issue có sẵn mà làm SHD Request?** — 4 lý do ở mục 8.2/M02: mốc SLA, lịch tính hạn, quan hệ yêu cầu–sự cố, khoảng chờ. Cộng thêm nhu cầu snapshot quyền lợi hợp đồng.
5. **Vì sao không dùng Asset cho máy khách?** — Asset là tài sản kế toán của công ty sở hữu; máy khách không phải tài sản của AIS. SHD Equipment là hồ sơ kỹ thuật thuần.
6. **Work Order của ERPNext dùng được cho sửa chữa không?** — Không, đó là lệnh sản xuất theo BOM. Dự án có `SHD Work Order` riêng cho hiện trường.
7. **Giữ chỗ vật tư khác xuất kho thế nào?** — Reservation là cam kết trừ vào *khả dụng* chứ không trừ tồn sổ sách; chỉ khi KTV tiêu hao tại visit mới sinh Stock Entry và Stock Ledger Entry thật.
8. **Làm sao hệ thống chống tạo trùng khi mạng chập chờn/gửi lại?** — Idempotency key + `SHD Command` + binding hash; cùng key cùng nội dung trả kết quả cũ, khác nội dung báo conflict; giao dịch rollback toàn bộ khi deadlock.
9. **Muốn thêm một trường vào Sales Invoice thì làm thế nào cho đúng?** — Custom Field (qua app/fixture hoặc `create_custom_fields` khi cài đặt) — không sửa DocType gốc trong thư mục erpnext, không sửa thẳng database.
10. **Phần AI của dự án ở mức nào?** — Thiết kế kiến trúc + contracts/schemas + conformance offline. Runtime chưa triển khai; catalog tri thức `SHD Knowledge` (không AI) đã chạy.

**Thuật ngữ tra nhanh:** Bench (bản cài Frappe) · Site (một hệ thống/DB độc lập) · Desk (giao diện quản trị) · DocType (khai báo đối tượng) · Document (một bản ghi) · Child Table (bảng con) · Custom Field (trường thêm vào DocType có sẵn) · Client/Server Script (script phía giao diện / phía máy chủ) · Hook (điểm móc logic của app) · Workflow (máy trạng thái duyệt) · Submittable (chứng từ có Submit/Cancel và `docstatus`) · Bin (tồn kho hiện tại theo Item×Warehouse) · Stock Ledger Entry (sổ cái kho) · SLA (cam kết mức dịch vụ) · PM (Preventive Maintenance — bảo trì phòng ngừa định kỳ) · FTFR (First-Time Fix Rate — tỉ lệ sửa đúng ngay lần đầu) · Idempotency (gửi lại không tạo trùng) · Fit–Gap (đối chiếu "có sẵn ↔ thiếu").

---

## PHỤ LỤC — CHỈ MỤC FILE ĐỂ ĐỌC TIẾP TRONG REPO

| Muốn hiểu | Đọc file |
|---|---|
| Toàn cảnh + vận hành lớp SHD | `README.md`, `docs/implementation/business_modules.md` |
| 28 DocType khai thế nào | `apps/smart_helpdesk/smart_helpdesk/schema.py` |
| App cài vào site ra sao | `apps/smart_helpdesk/smart_helpdesk/install.py`, `scripts/setup/install_business_app.py`, `docker/compose.business.yml` |
| Vì sao ghi dữ liệu chỉ qua API | `apps/smart_helpdesk/smart_helpdesk/api.py`, `core.py`, `security.py`, `hooks.py` |
| Luồng ca sửa end-to-end | `apps/smart_helpdesk/smart_helpdesk/operations.py` |
| SLA tính thế nào | `apps/smart_helpdesk/smart_helpdesk/sla.py` + `tests/test_calendar.py` |
| Thiết kế nghiệp vụ gốc M01–M10 | `docs/design/00_tong_quan_he_thong.md`, `docs/design/modules/m01..m10_*.md`, `docs/design/05_domain_workflow_contracts.md` |
| Lớp demo cũ trên native | `run_pipeline.py` (mục `--legacy-demo`), `scripts/setup/01..06`, `docs/reports/midterm_report.md` (Chương 5 cấu hình, Chương 7 Fit–Gap) |
| Thiết kế AI (chưa có runtime) | `docs/design/ai_architecture/readme.md` + 9 tài liệu con |
| Kiến trúc triển khai mục tiêu | `docs/design/07_kien_truc_trien_khai.md` |
| Bằng chứng kiểm thử | `data/business_validation.json`, `data/business_ui_validation.json` |

---

*Ghi chú nguồn: Toàn bộ thông tin về dự án trong file này được đọc trực tiếp từ mã nguồn, tài liệu và dữ liệu kiểm thử trong thư mục dự án trên máy của Bao ngày 28/10/2026 (không suy đoán từ slide). Các khẳng định về Frappe/ERPNext nói chung mô tả phiên bản v16 — đúng phiên bản dự án đang chạy. Chỗ nào tài liệu dự án tự ghi "chưa triển khai/hoãn", file này giữ nguyên trạng thái đó.*
