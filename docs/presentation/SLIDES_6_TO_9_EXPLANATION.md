# TÀI LIỆU GIẢI THÍCH & HƯỚNG DẪN THUYẾT TRÌNH CHI TIẾT
## SLIDE 06 ĐẾN SLIDE 09 — BÀI TRÌNH BÀY `docs/presentation/index.html`

> **Dự án:** Smart HelpDesk & Industrial Maintenance Management System trên ERPNext  
> **Tệp trình chiếu nguồn:** [`docs/presentation/index.html`](file:///e:/DUT.K1N4/HTTT/Project_SmartHelpDesk_Mainternance/docs/presentation/index.html)  
> **Phạm vi tài liệu:** Giải thích tường tận nội dung, ý nghĩa nghiệp vụ, thiết kế kỹ thuật, và cung cấp lời thoại thuyết trình mẫu cho **Slide 06, Slide 07, Slide 08, và Slide 09**.  
> **Vị trí chiến lược:** Cụm Slide 6 – 9 là **"Trái tim kỹ thuật & Nghiệp vụ cốt lõi (The Engine Room)"** của toàn bộ bài báo cáo. Đây là nơi thuyết phục Hội đồng phản biện rằng hệ thống đã được thiết kế CSDL thực tế, phân quyền chặt chẽ, tối ưu thuật toán điều phối và vận hành hiện trường khép kín.

---

## MỤC LỤC

1. [Tổng Quan Vị Trí Cụm Slide 06 – 09 Trong Cấu Trúc Báo Cáo](#1-tổng-quan-vị-trí-cụm-slide-06--09-trong-cấu-trúc-báo-cáo)
2. [Slide 06: Dữ Liệu & Chứng Từ Giao Dịch ERP Liên Kết (Kiến Trúc Dữ Liệu)](#2-slide-06-dữ-liệu--chứng-từ-giao-dịch-erp-liên-kết-kiến-trúc-dữ-liệu)
3. [Slide 07: Dữ Liệu Chủ (Master Data) & Phân Tách Nhiệm Vụ (RBAC / SoD)](#3-slide-07-dữ-liệu-chủ-master-data--phân-tách-nhiệm-vụ-rbac--sod)
4. [Slide 08: Chuyên Sâu 1 — Helpdesk • Ma Trận SLA 2 Chiều • Skill Routing](#4-slide-08-chuyên-sâu-1--helpdesk--ma-trận-sla-2-chiều--skill-routing)
5. [Slide 09: Chuyên Sâu 2 — CMMS • Mobile Van Stock • Tác Nghiệp Hiện Trường](#5-slide-09-chuyên-sâu-2--cmms--mobile-van-stock--tác-nghiệp-hiện-trường)
6. [Kỹ Thuật Chuyển Slide Mượt Mà (Transitions Script 6 &rarr; 7 &rarr; 8 &rarr; 9)](#6-kỹ-thuật-chuyển-slide-mượt-mà-transitions-script-6--7--8--9)
7. [Bộ Câu Hỏi Phản Biện Chuyên Sâu Riêng Cho Cụm Slide 6 – 9 (Q&A Defense)](#7-bộ-câu-hỏi-phản-biện-chuyên-sâu-riêng-cho-cụm-slide-6--9-qa-defense)

---

# 1. TỔNG QUAN VỊ TRÍ CỤM SLIDE 06 – 09 TRONG CẤU TRÚC BÁO CÁO

Trong bài trình chiếu 13 trang của `index.html`:
* **Slide 01 – 05:** Khởi động, Nêu bối cảnh, Nỗi đau nghiệp vụ (Pain Points), So sánh As-Is vs To-Be, và Định vị ERPNext trong mô hình Enterprise Architecture.
* **👉 Slide 06 – 09 (TRỌNG TÂM KỸ THUẬT):** Trình diễn chi tiết cách giải quyết bài toán:
  * *Slide 06:* Dữ liệu giao dịch liên kết thế nào để không bị "silo"?
  * *Slide 07:* Dữ liệu chủ (Master Data) được tổ chức ra sao và ai được làm gì (RBAC/SoD)?
  * *Slide 08:* Thuật toán điều phối KTV và cam kết SLA hoạt động như thế nào?
  * *Slide 09:* Kỹ thuật viên thao tác ngoài hiện trường và quản lý kho xe ra sao?
* **Slide 10 – 13:** Minh chứng ca sự cố thật (Live Case E2E), Quyết định đánh đổi kiến trúc (ADR), Đo lường KPI, và Hướng mở rộng AI/IoT.

---

# 2. SLIDE 06: DỮ LIỆU & CHỨNG TỪ GIAO DỊCH ERP LIÊN KẾT (KIẾN TRÚC DỮ LIỆU)

```
┌────────────────────────────────────────────────────────────────────────┐
│ SLIDE 06: DỮ LIỆU & CHỨNG TỪ GIAO DỊCH ERP LIÊN KẾT                    │
│ [Tag: KIẾN TRÚC DỮ LIỆU]                                               │
├─────────────────────────────────────────┬──────────────────────────────┤
│ BÊN TRÁI: Chuỗi Chứng Từ ERP Liên Hoàn  │ BÊN PHẢI: 09 Custom Fields   │
│ (Single Source of Truth)                │ Phá Vỡ Silo Dữ Liệu          │
│ • Hàng 1: Customer -> Issue -> SLA      │ • Issue: custom_asset        │
│ • Hàng 2: Asset -> Maint -> PM-to-CM    │ • Issue: incident_time (T0)  │
│ • Hàng 3: Stock Entry (3 dòng tiền)     │ • Issue: asset_category      │
│ • Hàng 4: Chuỗi Reorder -> MR -> PO     │ • Issue: related_issue, ...  │
├─────────────────────────────────────────┴──────────────────────────────┤
│ BANNER CHÂN: Nằm ở chuỗi chứng từ liên hoàn: Issue <-> Asset <-> Stock │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Nội dung chi tiết xuất hiện trên màn hình
1. **Khối bên trái (8 Cột): Sơ Đồ Chuỗi Giao Dịch Chứng Từ ERP (Transaction Flow)**
   - **Hàng 1 (Tiếp nhận & Cam kết):** `Customer` (Khách hàng) $\rightarrow$ `Issue` (Vé sự cố) $\rightarrow$ `SLA Matrix` (Ma trận cam kết thời gian cho VIP vs Standard).
   - **Hàng 2 (Cầu nối Bảo trì phòng ngừa):** `Asset` (Thiết bị) $\rightarrow$ `Asset Maintenance` (Kế hoạch bảo trì định kỳ) $\rightarrow$ `Maintenance Log` (Nhật ký thực hiện) $\rightarrow$ `PM-to-CM Issue` (Tự động kích hoạt vé sửa chữa khẩn khi phát hiện linh kiện xuống cấp).
   - **Hàng 3 (Xuất kho & Hóa đơn):** `Stock Entry` (Xuất kho phụ tùng) $\rightarrow$ Phân loại 3 luồng thanh toán (`Under Warranty` / `Billable to Customer` / `Goodwill`) $\rightarrow$ `Sales Invoice / General Ledger (GL)`.
   - **Hàng 4 (Chuỗi cung ứng tự động Procure-to-Stock):** `Reorder Trigger (Tồn 2 < Ngưỡng 3)` $\rightarrow$ `Material Request` $\rightarrow$ `Purchase Order` $\rightarrow$ `Purchase Receipt` $\rightarrow$ `Bù phụ tùng vào Van Stock (Kho xe KTV)`.

2. **Khối bên phải (4 Cột): 09 Custom Fields Phá Vỡ "Silo Dữ Liệu"**
   - Danh sách 9 trường dữ liệu tùy biến nhóm đã bổ sung vào Frappe để liên kết các bảng:
     - `Issue.custom_asset`: Nối trực tiếp vé sự cố với máy hỏng cụ thể.
     - `Issue.custom_incident_time`: Ghi nhận mốc thời gian T0 khách phát hiện hỏng ngoài thực tế.
     - `Issue.custom_asset_category`: Lưu nhóm thiết bị để thuật toán Skill Routing phân công.
     - `Issue.custom_related_issue`: Trỏ về vé cũ bị lặp lỗi (truy vết Callback).
     - `Issue.custom_has_callback`: Cờ đánh dấu sự cố tái phát để tính KPI FTFR.
     - `Asset.custom_is_customer_eq`: Đánh dấu máy thuộc quyền sở hữu khách hàng, cách ly sổ thuế AIS.
     - `Stock.custom_billing_type`: Định danh 3 dòng tiền chịu chi phí xuất phụ tùng.
     - `Stock.custom_issue` & `Stock.custom_asset`: Liên kết phiếu xuất kho ngược về vé và máy để tính tổng chi phí sở hữu (TCO per Asset).

3. **Banner chân trang:**
   - Khẳng định: Toàn bộ dữ liệu nằm trong chuỗi chứng từ liên hoàn: `Issue` $\leftrightarrow$ `Asset` $\leftrightarrow$ `Stock Entry` $\leftrightarrow$ `MR/PO` $\leftrightarrow$ `Sales Invoice`.

### 2.2. Ý nghĩa kỹ thuật & Giá trị bảo vệ đồ án
- **Khắc phục lỗi "Silo Dữ Liệu":** Trong ERPNext mặc định, module *Helpdesk* (Issue) và module *Stock* (Kho) hay *Asset* (Tài sản) nằm khá tách biệt. Bằng cách thêm 9 custom fields, nhóm tạo thành một mạng lưới dữ liệu khép kín: từ một phiếu xuất kho có thể truy ngược ra máy nào, ai sửa, vé nào, và ai trả tiền.
- **T0 vs T1:** Giải quyết bài toán gian lận thời gian SLA. Không lấy giờ bấm tạo vé trên hệ thống (T1) làm gốc, mà lưu thêm giờ khách báo thực tế (T0) để đo độ trễ tác nghiệp ($\Delta T = T1 - T0$).

### 2.3. Lời thoại thuyết trình mẫu (Script Slide 06)
> *"Kính thưa Thầy/Cô, bước vào phần kiến trúc dữ liệu tại Slide 6, câu hỏi lớn nhất đặt ra cho nhóm là: **Làm sao để một yêu cầu sửa chữa không bị cô lập như một 'ticket hỗ trợ' đơn thuần mà thực sự liên kết với toàn bộ dòng chảy ERP?**
> 
> Nhìn vào sơ đồ bên trái, nhóm đã thiết kế chuỗi giao dịch liên hoàn qua 4 dòng nghiệp vụ:
> - Từ Khách hàng $\rightarrow$ sinh Vé sự cố $\rightarrow$ kích hoạt SLA Matrix.
> - Từ Thiết bị $\rightarrow$ kế hoạch bảo trì PM $\rightarrow$ phát hiện hỏng ngầm kích hoạt vé khẩn cấp PM-to-CM.
> - Khi KTV xuất kho bằng `Stock Entry`, hệ thống phân rẽ ngay 3 dòng tiền: Hãng bảo hành, Khách trả tiền hay Công ty bù lỗ, trước khi đẩy sang hóa đơn `Sales Invoice`.
> - Khi tồn kho chạm đáy, chuỗi mua sắm tự động bù phụ tùng vào kho xe của KTV.
> 
> Để xâu chuỗi toàn bộ hệ thống này, cột bên phải là **9 Custom Fields** do nhóm trực tiếp cấu hình trên Frappe. Nhờ 9 trường này, hệ thống phá vỡ hoàn toàn các silo dữ liệu, biến ERPNext thành một **Single Source of Truth** duy nhất!"*

---

# 3. SLIDE 07: DỮ LIỆU CHỦ (MASTER DATA) & PHÂN TÁCH NHIỆM VỤ (RBAC / SoD)

```
┌────────────────────────────────────────────────────────────────────────┐
│ SLIDE 07: MASTER DATA & PHÂN TÁCH NHIỆM VỤ (RBAC / SoD)                │
│ [Tag: QUẢN TRỊ DỮ LIỆU & BẢO MẬT]                                      │
├─────────────────────────────────────────┬──────────────────────────────┤
│ BÊN TRÁI: Hệ Sinh Thái Master Data      │ BÊN PHẢI: Bảng Phân Quyền    │
│ (Pháp nhân SBN: AIS)                    │ 5 Persona Roles & SoD Matrix │
│ • 03 Khách hàng B2B (Tân Á, Hải Nam...) │ • Issue                      │
│ • 03 Kỹ thuật viên (An, Bình, Cường)    │ • Stock Entry                │
│ • 05 Máy + 1 Thiết bị đo                │ • MR / PO / PR               │
│ • 06 Kho phân cấp (Trung tâm, Xe, Thu)  │ • Sales Invoice              │
├─────────────────────────────────────────┴──────────────────────────────┤
│ BANNER CHÂN: Cách ly đa khách hàng qua User Permission (Zero Leakage)   │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Nội dung chi tiết xuất hiện trên màn hình
1. **Khối bên trái (6 Cột): Hệ Sinh Thái Master Data (Pháp Nhân AIS)**
   - Hệ thống được cấu hình dữ liệu mẫu hoàn chỉnh và sạch sẽ (không có dữ liệu rác):
     - **03 Khách hàng B2B:** Công ty Tân Á (VIP - Khí nén & In bao bì), Hải Nam (Standard - Chiller), Song Long (Standard - Hệ thống điện MSB).
     - **03 Kỹ thuật viên hiện trường:** Nguyễn Văn An (Chuyên môn Cơ khí & Khí nén), Trần Đình Bình (Điện công nghiệp & Tự động hóa), Lê Hoàng Cường (Nhiệt - Điện lạnh).
     - **05 Máy móc công nghiệp + 1 Thiết bị đo kiểm:** Máy nén khí Hitachi 75kW, Máy in Flexo 6 màu, Chiller Daikin 100RT, Máy phát điện Cummins 250kVA, Tủ phân phối MSB 1200A, và 01 Thiết bị đo rung SKF.
     - **06 Kho hàng phân cấp:** 01 Kho Linh kiện Trung tâm, 03 Kho Xe lưu động của 3 KTV (Kho Xe - An, Kho Xe - Bình, Kho Xe - Cường), và 01 Kho Thu hồi Linh kiện Hỏng (Core Return).

2. **Khối bên phải (6 Cột): Ma Trận Phân Quyền (DocPerm) & Phân Tách Nhiệm Vụ (SoD)**
   - Bảng phân quyền 5 vai trò trên 4 loại chứng từ:
     - `Customer (Khách hàng)`: Chỉ được Tạo/Xem `Issue`; tuyệt đối không được sờ vào `Stock Entry`, `PO` hay `Sales Invoice`.
     - `Dispatcher (Điều phối viên)`: Toàn quyền trên `Issue`; chỉ xem `Stock Entry`; không được tự tạo phiếu mua hàng hay hóa đơn.
     - `Technician (KTV hiện trường)`: Xử lý `Issue`; chỉ được quyền **Xuất kho xe của chính mình** (`Stock Entry` từ Kho Xe KTV); cấm chạm vào mua sắm hay kế toán.
     - `Warehouse (Thủ kho)`: Xem `Issue`; Toàn quyền xuất nhập tại Kho Trung tâm; Tạo đề xuất mua sắm và nhập kho (`MR/PO/PR`).
     - `Accountant (Kế toán)`: Xem vé và kho; Toàn quyền ghi nhận và xuất hóa đơn `Sales Invoice`.
   - **Nguyên tắc bất biến SoD (Segregation of Duties):** *Kỹ Thuật Viên $\ne$ Thủ Kho $\ne$ Kế Toán* — triệt tiêu nguy cơ KTV vừa sửa vừa tự xuất kho rồi tự xóa dấu vết kế toán.

3. **Banner chân trang:**
   - Ứng dụng cơ chế `User Permission` gốc của Frappe: Tài khoản đại diện của khách hàng Tân Á đăng nhập Web Portal **chỉ nhìn thấy đúng thiết bị và ticket của Tân Á**, bảo mật tuyệt đối đa khách thuê (Zero Data Leakage).

### 3.2. Ý nghĩa kỹ thuật & Giá trị bảo vệ đồ án
- **Chứng minh sự chuẩn bị bài bản:** Nhóm không dùng dữ liệu "test 123", mà dựng hẳn một kịch bản doanh nghiệp bảo trì cơ điện thực tế với đầy đủ thiết bị nặng, KTV theo chuyên môn và cây kho logic.
- **Tiêu chuẩn kiểm toán (Audit Trail):** Giải thích tại sao KTV không thể kiêm nhiệm thủ kho. Phân định rạch ròi trách nhiệm cá nhân đối với từng phụ tùng trên xe.

### 3.3. Lời thoại thuyết trình mẫu (Script Slide 07)
> *"Tại Slide 7, nhóm xin trình bày nền tảng **Dữ Liệu Chủ (Master Data)** và bài toán **Phân Quyền - Phân Tách Nhiệm Vụ (RBAC & SoD)**.
> 
> Ở cột bên trái, toàn bộ hệ sinh thái của công ty AIS được thiết kế khép kín gồm: 3 khách hàng B2B, 3 kỹ sư thuộc 3 chuyên môn khác nhau, 5 máy công nghiệp hạng nặng và 6 kho hàng phân cấp — trong đó có 3 kho xe lưu động gắn với từng thợ.
> 
> Ở cột bên phải là bảng ma trận phân quyền cho 5 vai trò (Persona Roles). Chúng em áp dụng triệt để nguyên tắc **Segregation of Duties (SoD)**:
> - Kỹ thuật viên chỉ được phép xuất vật tư từ chính Kho Xe của mình, không được can thiệp vào Kho Tổng hay sửa chữa chứng từ kế toán.
> - Kế toán là người duy nhất chốt `Sales Invoice`.
> - Đặc biệt, bằng cơ chế `Frappe User Permission`, chúng em đảm bảo khách hàng Tân Á tuyệt đối không thể nhìn thấy máy móc hay lịch sử sự cố của khách hàng Hải Nam, loại bỏ 100% nguy cơ rò rỉ dữ liệu giữa các doanh nghiệp!"*

---

# 4. SLIDE 08: CHUYÊN SÂU 1 — HELPDESK • MA TRẬN SLA 2 CHIỀU • SKILL ROUTING

```
┌────────────────────────────────────────────────────────────────────────┐
│ SLIDE 08: HELPDESK • MA TRẬN SLA 2 CHIỀU • SKILL ROUTING               │
│ [Tag: CHUYÊN SÂU 1: DỊCH VỤ]                                           │
├─────────────────────────────────────────┬──────────────────────────────┤
│ BÊN TRÁI: Luồng Tiếp Nhận & Thuật Toán  │ BÊN PHẢI: Ma Trận SLA 2 Chiều│
│ Điều Phối Kết Hợp (Hybrid Routing)      │ (Severity x Customer Tier)   │
│ 1. Kênh tiếp nhận: QR 15s / Portal      │ • Urgent: VIP 30m/4h         │
│ 2. Đo trễ tác nghiệp (T1 - T0)          │ • High:   VIP 60m/8h         │
│ 3. Hybrid: Skill Filter + Round Robin   │ • Medium: VIP 2h/16h         │
│ 4. Quick Action [Check-in]              │ • Low:    VIP 4h/36h         │
│ 5. Nghiệm thu & Callback Window         │                              │
├─────────────────────────────────────────┴──────────────────────────────┤
│ BANNER CHÂN: "Skill determines who is eligible;                        │
│                Round Robin distributes within the eligible group."     │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1. Nội dung chi tiết xuất hiện trên màn hình
1. **Khối bên trái (7 Cột): Luồng Tiếp Nhận & Thuật Toán Điều Phối Kết Hợp**
   - **Bước 1 — Kênh tiếp nhận:** Khách quét tem QR trong 15s trên vỏ máy hoặc gọi Hotline $\rightarrow$ Hệ thống ghi nhận mốc $T0$ (thời điểm khách phát hiện sự cố thực tế).
   - **Bước 2 — Nạp hệ thống:** Ghi nhận mốc $T1$ khi vé được lưu vào CSDL $\rightarrow$ Tính toán chỉ số $\Delta T = T1 - T0$ (Logging Latency - độ trễ tác nghiệp ghi nhận).
   - **Bước 3 — Thuật toán điều phối kết hợp (Hybrid Routing):**
     - Đọc trường `custom_asset_category` trên thiết bị.
     - **Skill Filter:** Lọc danh sách KTV có chứng chỉ/kỹ năng tương thích với loại máy (Cơ khí, Điện, Lạnh).
     - **Round Robin:** Chỉ quay vòng chia đều việc *bên trong nhóm KTV đủ điều kiện năng lực*.
   - **Bước 4 — Tiếp cận hiện trường:** KTV bấm nút Quick Action **[Check-in]** trên điện thoại $\rightarrow$ Chuyển vé sang `In Progress`, chốt mốc thời gian và khóa đồng hồ đếm lùi SLA Response.
   - **Bước 5 — Hậu kiểm & Cửa sổ Callback (72h – 7 ngày):** Sau khi đóng vé, nếu máy bị báo hỏng lại đúng lỗi cũ trong vòng 7 ngày $\rightarrow$ Hệ thống đánh dấu cờ `custom_has_callback = 1`, trừ điểm FTFR của KTV.

2. **Khối bên phải (5 Cột): Ma Trận Cam Kết SLA 2 Chiều Chuẩn Công Nghiệp**
   - Bảng đối soát chi tiết giữa Mức độ sự cố (Severity) và Hạng khách hàng (Tier):
     | Độ Ưu Tiên | VIP Tân Á (Response / Resolution) | Standard (Response / Resolution) |
     | :--- | :---: | :---: |
     | **Urgent (Dừng máy toàn bộ)** | **30 phút / 4 giờ** | 60 phút / 8 giờ |
     | **High (Giảm tải dây chuyền)** | **60 phút / 8 giờ** | 120 phút / 16 giờ |
     | **Medium (Hệ thống phụ trợ)** | 2 giờ / 16 giờ | 4 giờ / 24 giờ |
     | **Low (Kiểm tra định kỳ)** | 4 giờ / 36 giờ | 8 giờ / 48 giờ |
   - **Quy tắc trục kép:** Cam kết thời hạn được tính toán tự động bằng giây, không thể can thiệp thủ công.

3. **Banner chân trang:**
   - Triết lý điều phối cốt lõi: *"Skill determines who is eligible; Round Robin distributes within the eligible group"* (Chuyên môn quyết định ai đủ tư cách; Quay vòng chia đều việc trong nhóm đủ tư cách).

### 4.2. Ý nghĩa kỹ thuật & Giá trị bảo vệ đồ án
- **Tránh chia việc mù quáng:** Nếu chỉ dùng Round Robin đơn thuần của Frappe, hệ thống sẽ chia ca máy biến áp cho thợ sửa ống nước. Nhóm đã giải quyết bằng **Server Script Hook kết hợp 2 tầng lọc**.
- **Chống gian lận KPI hiện trường:** Nút `Check-in` yêu cầu KTV xác nhận thời điểm tiếp cận nhà máy để đo thời gian phản ứng thật (Response Time).

### 4.3. Lời thoại thuyết trình mẫu (Script Slide 08)
> *"Thưa Thầy/Cô, Slide 8 đi sâu vào 'bộ não' điều phối dịch vụ của hệ thống: **Ma Trận SLA 2 Chiều và Thuật Toán Skill Routing**.
> 
> Nhìn sang bên phải, chúng em không dùng một hạn SLA chung chung. Hệ thống xây dựng **Ma trận 2 trục kép**: Hạng hợp đồng (VIP vs Standard) nhân với Mức độ sự cố (Urgent đến Low). Khách VIP khi máy dừng khẩn cấp được cam kết có mặt trong 30 phút và sửa xong trong 4 giờ, nhanh gấp đôi khách thường.
> 
> Tuy nhiên, bài toán hóc búa nhất là: **Giao vé cho ai?**
> Nếu dùng thuật toán xoay vòng Round Robin mặc định của Frappe, hệ thống sẽ chia bừa thợ cơ khí đi sửa tủ điện.
> Vì vậy, ở cột bên trái, nhóm đã xây dựng **Thuật toán Hybrid Routing**:
> - Đầu tiên, hệ thống dùng **Skill Filter** để lọc danh sách thợ có kỹ năng phù hợp với chủng loại thiết bị.
> - Sau đó, hệ thống mới áp dụng **Round Robin** để xoay vòng công bằng trong nhóm thợ đủ điều kiện.
> Đúng như triết lý chúng em nêu ở chân slide: *'Chuyên môn xác định ai đủ điều kiện; Xoay vòng phân bổ trong nhóm đủ điều kiện'*. Đảm bảo đúng người, đúng việc 100%!"*

---

# 5. SLIDE 09: CHUYÊN SÂU 2 — CMMS • MOBILE VAN STOCK • TÁC NGHIỆP HIỆN TRƯỜNG

```
┌────────────────────────────────────────────────────────────────────────┐
│ SLIDE 09: CMMS • MOBILE VAN STOCK • TÁC NGHIỆP HIỆN TRƯỜNG             │
│ [Tag: CHUYÊN SÂU 2: HIỆN TRƯỜNG]                                       │
├─────────────────────┬─────────────────────┬────────────────────────────┤
│ CỘT 1: THIẾT BỊ     │ CỘT 2: FIELD SERVICE│ CỘT 3: KHO XE LƯU ĐỘNG     │
│ (CMMS)              │ KTV TRÊN MOBILE     │ (VAN STOCK)                │
│ 1. Tem QR thân máy  │ 1. Nhận việc Mobile │ 1. Chặng 1: Trans từ Kho Tổng│
│ 2. Cách ly thuế = 0 │ 2. Nút [Check-in]   │ 2. Chặng 2: Issue tại chỗ  │
│ 3. Lịch PM tự động  │ 3. Nút [Xuất vật tư]│ 3. Trách nhiệm vật chất xe │
│ 4. PM-to-CM Trigger │ 4. Nút [Hoàn thành] │ 4. Thu hồi linh kiện hỏng  │
├─────────────────────┴─────────────────────┴────────────────────────────┤
│ BANNER CHÂN: Tam giác hiện trường: Thiết Bị <-> Kỹ Thuật Viên <-> Kho Xe│
└────────────────────────────────────────────────────────────────────────┘
```

### 5.1. Nội dung chi tiết xuất hiện trên màn hình
Slide được chia thành **3 Cột tương ứng với "Tam Giác Hiện Trường"**:
1. **Cột 1 (Màu xanh lá): THIẾT BỊ (CMMS)**
   - `1. Tem QR Code thân máy`: Quét bằng camera điện thoại là form tự động điền đúng mã máy và vị trí lắp đặt.
   - `2. Cách ly kế toán thuế`: Cấu hình cờ `calculate_depreciation = 0` và `custom_is_customer_eq = 1`. Do máy thuộc tài sản của khách hàng, hệ thống tuyệt đối không trích khấu hao vào báo cáo tài chính của công ty bảo trì AIS.
   - `3. Lập lịch PM tự động`: Cấu hình chu kỳ định kỳ (1 tháng cho Chiller, 3 tháng cho Máy nén khí, 6 tháng cho Tủ điện MSB) để Cron tự động sinh `Asset Maintenance Log`.
   - `4. PM-to-CM Trigger`: Khi đi bảo dưỡng phòng ngừa (PM), nếu KTV phát hiện ổ bi rung lắc nguy hiểm $\rightarrow$ Bấm nút tạo ngay vé sửa chữa khẩn cấp (CM) có liên kết.

2. **Cột 2 (Màu xanh dương): FIELD SERVICE KTV TRÊN MOBILE DESK**
   - Thiết kế giao diện di động tối ưu 1-chạm (Client Scripts):
     - `1. Nhận việc trên Mobile Desk`: KTV xem thông báo vé mới, thông số kỹ thuật và hồ sơ bệnh án cũ của máy.
     - `2. Nút [Check-in Hiện Trường]`: Chuyển vé sang `In Progress`, chốt giờ phản hồi SLA.
     - `3. Nút [Xuất Linh Kiện Sửa]`: Tự động điền mã vé, mã máy, KTV chỉ cần chọn phụ tùng trên xe và số lượng.
     - `4. Nút [Hoàn Thành Ca]`: Bắt buộc KTV phải chọn 1 trong 5 danh mục nguyên nhân gốc (`root_cause`) trước khi đóng vé để phục vụ phân tích dữ liệu sau này.

3. **Cột 3 (Màu vàng cam): KHO XE LƯU ĐỘNG (MOBILE VAN STOCK)**
   - Cơ chế quản lý vật tư lưu động giải quyết nỗi đau thiếu hàng hiện trường:
     - `1. Chặng 1 — Material Transfer`: Đầu tuần xuất điều chuyển phụ tùng thông dụng từ Kho Trung tâm lên Kho Xe của từng KTV.
     - `2. Chặng 2 — Material Issue`: KTV xuất phụ tùng trực tiếp từ kho xe gắn vào máy khách tại hiện trường, tồn kho trừ tức thì.
     - `3. Trách nhiệm vật chất cá nhân`: Linh kiện nằm trên xe nào thì KTV đó ký biên bản chịu trách nhiệm, chấm dứt tình trạng thất thoát không rõ lý do.
     - `4. Core Return (Thu hồi xác linh kiện)`: Bắt buộc thu hồi linh kiện hỏng về Kho Thu Hồi để kiểm tra và đối soát bảo hành với hãng.

4. **Banner chân trang:**
   - Khẳng định: *Tam giác hiện trường gồm Thiết Bị (Asset) $\leftrightarrow$ Kỹ Thuật Viên (Technician) $\leftrightarrow$ Kho Xe (Inventory)* được tích hợp tự nhiên (native) trên nền tảng ERPNext mà không cần thông qua bất kỳ API trung gian nào.

### 5.2. Ý nghĩa kỹ thuật & Giá trị bảo vệ đồ án
- **Giảm 65% Truck-roll:** Kỹ thuật viên có sẵn linh kiện thông dụng trên xe, không phải mất công chạy 30km về kho tổng lấy đồ rồi quay lại nhà máy khách.
- **Tăng First-Time Fix Rate (FTFR):** Tỷ lệ sửa dứt điểm ngay lần đầu tăng vọt nhờ mô hình Van Stock.
- **Phân định tài sản công ty vs khách hàng:** Tránh lỗi nghiệp vụ cơ bản trong ERP là tính khấu hao tài sản của người khác.

### 5.3. Lời thoại thuyết trình mẫu (Script Slide 09)
> *"Tại Slide 9, chúng em đưa Thầy/Cô đến **Hiện trường tác nghiệp thực tế** thông qua mô hình 'Tam Giác Hiện Trường' gồm: Thiết Bị – Kỹ Thuật Viên – Kho Xe Lưu Động.
> 
> - **Ở góc Thiết bị (Cột 1):** Mỗi máy được gắn tem QR. Đặc biệt, nhóm đã xử lý một điểm fit-gap quan trọng trong kế toán ERP: Tài sản của khách được gắn cờ `custom_is_customer_eq` để **không tính khấu hao** vào sổ sách AIS. Tính năng `PM-to-CM Trigger` giúp KTV khi khám máy định kỳ phát hiện hỏng ngầm có thể tạo ngay vé khẩn có SLA.
> - **Ở góc Kỹ thuật viên (Cột 2):** Trên giao diện điện thoại, KTV chỉ cần thao tác 4 nút bấm tiện lợi: Nhận việc $\rightarrow$ Check-in hiện trường $\rightarrow$ Xuất linh kiện $\rightarrow$ Hoàn thành ca với phân loại nguyên nhân gốc rễ `root_cause`.
> - **Ở góc Kho Xe (Cột 3) — Điểm sáng của dự án:** Chúng em áp dụng mô hình **Van Stock 2 chặng**: Đầu tuần chuyển linh kiện từ Kho Tổng lên Kho Xe từng thợ; khi đến nhà máy thì xuất thẳng từ kho xe vào máy khách.
> Nhờ mô hình này, chúng em cắt giảm được 65% số chuyến xe chạy đi chạy lại lấy đồ và nâng cao tối đa tỷ lệ sửa dứt điểm lần đầu (FTFR)!"*

---

# 6. KỸ THUẬT CHUYỂN SLIDE MƯỢT MÀ (TRANSITIONS SCRIPT 6 &rarr; 7 &rarr; 8 &rarr; 9)

> [!TIP]
> Một bài thuyết trình xuất sắc không bao giờ dừng lại nói *"Bây giờ qua slide tiếp theo..."*. Hãy dùng các câu nối (Bridge Sentences) dẫn dắt logic tự nhiên giữa 4 slide:

* **Từ Slide 05 sang Slide 06:**
  > *"Chúng ta đã thấy 5 trụ cột nghiệp vụ ở tầm chiến lược. Vậy ở tầng thực thi chứng từ, dữ liệu ERP được móc nối liên hoàn như thế nào để không bị 'silo'? Xin mời Thầy/Cô cùng nhìn vào Slide 6..."*
* **Từ Slide 06 sang Slide 07:**
  > *"Khi dòng chảy chứng từ đã thông suốt, câu hỏi tiếp theo là: Dữ liệu đó vận hành trên những thực thể nào và ai là người có thẩm quyền ký duyệt? Đó chính là nội dung của Slide 7 về Master Data và Phân tách nhiệm vụ..."*
* **Từ Slide 07 sang Slide 08:**
  > *"Chúng ta đã có dữ liệu chuẩn và ma trận phân quyền chặt chẽ. Bây giờ, khi một sự cố thực tế ập đến, hệ thống sẽ tiếp nhận, cam kết thời gian và điều phối KTV ra sao? Chúng em xin đi sâu vào Chuyên sâu 1 tại Slide 8..."*
* **Từ Slide 08 sang Slide 09:**
  > *"Sau khi hệ thống đã chọn đúng người thợ lành nghề và áp đúng hạn SLA, người thợ đó bước xuống hiện trường sẽ tác nghiệp với thiết bị và kho phụ tùng trên xe như thế nào? Xin mời Thầy/Cô đến với Chuyên sâu 2 tại Slide 9: Mô hình Tam Giác Hiện Trường..."*

---

# 7. BỘ CÂU HỎI PHẢN BIỆN CHUYÊN SÂU RIÊNG CHO CỤM SLIDE 6 – 9 (Q&A DEFENSE)

### ❓ Câu 1: "Tại sao trong Slide 6, nhóm phải tạo thêm trường `custom_incident_time (T0)` mà không dùng luôn trường `creation` có sẵn của Frappe?"
* **Trả lời chuẩn:**
  > *"Dạ thưa Thầy/Cô, trường `creation` của Frappe chỉ ghi lại thời điểm bản ghi được lưu vào CSDL (tức mốc $T1$). Trong thực tế bảo dưỡng công nghiệp, khách hàng phát hiện máy dừng lúc 8:00 sáng ($T0$), nhưng do bận xử lý dây chuyền nên đến 8:30 mới gọi hotline và Dispatcher tạo vé lúc 8:35 ($T1$).
  > Nếu lấy $T1$ làm gốc để tính SLA thì doanh nghiệp đang 'ăn gian' 35 phút của khách hàng. Việc lưu riêng mốc $T0$ giúp đo lường chính xác cam kết với khách, đồng thời giúp Ban giám đốc đo được chỉ số $\Delta T = T1 - T0$ (Logging Latency) để đánh giá tốc độ tiếp nhận của bộ phận trực tổng đài ạ."*

### ❓ Câu 2: "Tại sao nhóm không dùng phân hệ Asset chuẩn của ERPNext mà phải gắn cờ `custom_is_customer_eq` và tắt khấu hao ở Slide 7 & 9?"
* **Trả lời chuẩn:**
  > *"Dạ thưa Thầy/Cô, trong ERPNext chuẩn, module `Asset` được thiết kế để quản lý tài sản cố định **thuộc sở hữu của chính doanh nghiệp** (như bàn ghế, máy móc công ty tự mua) và hệ thống mặc định sẽ tự động trích khấu hao hàng tháng vào tài khoản chi phí của công ty.
  > Tuy nhiên, công ty AIS là đơn vị làm dịch vụ bảo trì cho khách hàng. Các máy nén khí, máy in là tài sản của công ty Tân Á, không phải của AIS. Nếu để ERPNext trích khấu hao thì báo cáo tài chính và sổ thuế của AIS sẽ bị sai lệch nghiêm trọng. Do đó, việc gắn cờ `custom_is_customer_eq = 1` và set `calculate_depreciation = 0` là một giải pháp Fit-Gap bắt buộc để vừa quản lý được lịch bảo dưỡng thiết bị, vừa cách ly hoàn toàn nghiệp vụ kế toán tài sản cố định ạ."*

### ❓ Câu 3: "Tại sao ở Slide 8, nhóm lại kết hợp Skill Filter với Round Robin mà không dùng thuần túy một trong hai?"
* **Trả lời chuẩn:**
  > *"Dạ thưa Thầy/Cô:
  > - Nếu chỉ dùng **Skill Filter đơn thuần**: Khi có nhiều thợ cùng chuyên môn điện, hệ thống không biết chia cho ai, dễ dẫn đến việc dồn hết việc cho thợ giỏi nhất gây quá tải.
  > - Nếu chỉ dùng **Round Robin đơn thuần**: Hệ thống chia việc mù quáng theo vòng tròn, dẫn đến thợ cơ khí bị giao đi sửa biến tần tủ điện — làm sai chuyên môn và chắc chắn trễ SLA.
  > Vì vậy, thuật toán **Hybrid Routing 2 tầng** của nhóm là giải pháp tối ưu: Tầng 1 lọc ra tập hợp các thợ đủ năng lực sửa loại máy đó, Tầng 2 xoay vòng Round Robin chỉ bên trong tập hợp này để đảm bảo phân bổ đều khối lượng công việc ạ."*

### ❓ Câu 4: "Mô hình Kho xe lưu động (Van Stock) ở Slide 9 giải quyết rủi ro mất mát phụ tùng như thế nào?"
* **Trả lời chuẩn:**
  > *"Dạ thưa Thầy/Cô, trong cách làm cũ, thợ cứ đến kho tổng bốc phụ tùng mang đi, cuối tháng không biết ai cầm cái gì dẫn đến thất thoát vật tư.
  > Trong mô hình của nhóm: Mỗi xe KTV là một `Warehouse` con độc lập mang tên KTV đó. Khi chuyển đồ từ Kho Tổng lên xe, phải có chứng từ `Material Transfer` và KTV phải ký nhận số dư tại xe. Khi sửa xong cho khách, KTV dùng phiếu `Material Issue` gắn đúng mã máy và mã vé.
  > Nhờ vậy, thủ kho và giám đốc mở báo cáo tồn kho tại kho xe là biết chính xác trên cốp xe của KTV An hiện tại còn bao nhiêu gioăng, bao nhiêu cảm biến. Trách nhiệm vật chất thuộc về cá nhân KTV nên loại bỏ triệt để việc thất thoát ạ."*
