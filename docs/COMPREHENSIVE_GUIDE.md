# CẨM NANG TOÀN DIỆN: GIẢI MÃ DỰ ÁN SMART HELPDESK & MAINTENANCE TRÊN ERPNEXT
> **Tài liệu hướng dẫn từ A đến Z dành cho:** Thành viên dự án, Người mới bắt đầu với ERPNext, và Hội đồng đánh giá đồ án.  
> **Dự án:** Triển khai Hệ thống Smart Helpdesk & Quản trị Bảo trì Công nghiệp (Field Service Management & MRO)  
> **Nền tảng:** ERPNext v16 / Frappe Framework  
> **Đơn vị thực hiện:** Nhóm sinh viên DUT.K1N4 — Đề tài Hệ Thống Thông Tin  

---

## MỤC LỤC
1. [Phần 1: Nhập môn cho người chưa từng dùng ERPNext (Mental Model)](#phần-1-nhập-môn-cho-người-chưa-từng-dùng-erpnext-mental-model)
2. [Phần 2: Bức tranh Domain & Bản đồ Chức năng Tổng thể (Domain Blueprint)](#phần-2-bức-tranh-domain--bản-đồ-chức-năng-tổng-thể-domain-blueprint)
3. [Phần 3: Phân tích 8 Nỗi đau Doanh nghiệp Thực tế (8 Comprehensive Pain Points)](#phần-3-phân-tích-8-nỗi-đau-doanh-nghiệp-thực-tế-8-comprehensive-pain-points)
4. [Phần 4: Bản phân tích Đánh đổi Kiến trúc (Architecture Decision Records & Trade-offs)](#phần-4-bản-phân-tích-đánh-đổi-kiến-trúc-architecture-decision-records--trade-offs)
5. [Phần 5: Cẩm nang Thao tác Giao diện ERPNext (Click-by-Click UI Walkthrough)](#phần-5-cẩm-nang-thao-tác-giao-diện-erpnext-click-by-click-ui-walkthrough)
6. [Phần 6: Đào sâu Tối ưu hóa Hệ thống Hiện tại (Deep-Dive Optimization)](#phần-6-đào-sâu-tối-ưu-hóa-hệ-thống-hiện-tại-deep-dive-optimization)
7. [Phần 7: Lộ trình Mở rộng & Scale Quy mô Tương lai (Future Roadmap)](#phần-7-lộ-trình-mở-rộng--scale-quy-mô-tương-lai-future-roadmap)

---

## PHẦN 1: NHẬP MÔN CHO NGƯỜI CHƯA TỪNG DÙNG ERPNEXT (MENTAL MODEL)

### 1.1. Bản chất: Frappe Framework vs. ERPNext là gì?
Để không bị ngợp giữa hàng trăm tính năng, bạn cần hiểu rõ sự phân tầng:
* **Frappe Framework (Cái Khung Gầm - Engine):**
  * Tương tự như Laravel trong PHP hay Django trong Python, nhưng Frappe đi kèm sẵn một **hệ điều hành web thu nhỏ**.
  * Frappe chịu trách nhiệm: Quản lý cơ sở dữ liệu (Database MariaDB/PostgreSQL), vẽ giao diện người dùng (gọi là **Desk**), cơ chế xác thực/tài khoản, hệ thống phân quyền (Role & Permissions), thanh tìm kiếm toàn cục (`Ctrl + K`), và các cổng giao tiếp REST API. Bản thân Frappe **hoàn toàn không chứa nghiệp vụ kinh doanh** nào cả.
* **ERPNext (Ứng dụng Chạy trên Frappe):**
  * Là một bộ ứng dụng quản trị doanh nghiệp mã nguồn mở khổng lồ được xây dựng bằng Frappe.
  * ERPNext mang đến các module quản lý phòng ban: Kế toán (`Accounting`), Mua hàng (`Buying`), Bán hàng (`Selling`), Quản lý kho (`Stock`), Tài sản (`Assets`), Nhân sự (`HR`), và Dịch vụ hỗ trợ (`Support`).

### 1.2. Tại sao doanh nghiệp dùng ERPNext thay vì tự code Web từ đầu?
* **Tư duy tự code Web App (Custom Development):**
  * Khi máy hỏng $\rightarrow$ Viết code lưu vào bảng `Issues`.
  * Khi KTV thay lọc dầu $\rightarrow$ Lưu dòng chữ "Đã thay 2 lọc dầu".
  * *Hạn chế:* Hệ thống này là một "hòn đảo thông tin cô lập". Nó không biết 2 cái lọc dầu đó từ kho nào xuất ra, giá trị bao nhiêu tiền, ai chịu chi phí, và kho còn đủ đồ để chạy sự cố tiếp theo hay không.
* **Tư duy Hệ thống ERP (Enterprise Resource Planning):**
  * Một hành động kỹ thuật ở hiện trường (thay 2 cái lọc dầu) sẽ lập tức kích hoạt chuỗi phản ứng liên phòng ban:
    1. **Kho (`Stock`):** Tồn kho giảm từ 4 xuống 2 cái; cảnh báo thủ kho nhập thêm hàng vì đã dưới mức an toàn (Reorder Level = 3).
    2. **Kế toán (`Accounting`):** Sổ cái ghi giảm giá trị tài sản kho 1.300.000 VNĐ; hạch toán vào chi phí bảo hành của hợp đồng tương ứng.
    3. **Tài sản (`Assets`):** Máy móc ghi nhận một ca thay thế phụ tùng, phục vụ tính tổng chi phí sở hữu (TCO).
  * 👉 **ERP đảm bảo tính toàn vẹn dữ liệu xuyên suốt (Single Source of Truth), không một dữ liệu nào bị rời rạc.**

### 1.3. Bảng thuật ngữ cơ bản cần nắm
| Thuật ngữ | Ý nghĩa trong ERPNext | Tương đương trong lập trình truyền thống |
| :--- | :--- | :--- |
| **DocType** | Định nghĩa một cấu trúc thực thể/bảng dữ liệu | Database Table + Model + Form Schema |
| **Desk** | Bàn làm việc chính chứa các Workspace | Admin Dashboard / Portal |
| **List View** | Giao diện danh sách các bản ghi | Data Table / Index View |
| **Form View** | Giao diện xem và chỉnh sửa chi tiết một bản ghi | Detail / Edit Form |
| **Custom Field** | Trường dữ liệu tự tạo thêm vào DocType có sẵn | `ALTER TABLE ADD COLUMN` |
| **Client Script** | Đoạn code JavaScript chạy trên trình duyệt người dùng | Frontend Event Handlers / UI Hook |
| **Server Script** | Đoạn code Python chạy trong sandbox server | Backend Trigger / Database Hook |
| **Assignment Rule** | Luật tự động gán tài liệu cho nhân sự | Routing / Dispatching Engine |

### 1.4. Bảng Đối Chiếu: "Cái gì có sẵn" vs. "Cái gì nhóm đã cấu hình/tùy biến"
| Phân hệ | ERPNext Có Sẵn (Native) | Nhóm Đã Cấu Hình / Tùy Biến (Custom) |
| :--- | :--- | :--- |
| **Helpdesk & SLA** | • Bảng `Issue` để tiếp nhận yêu cầu.<br>• Mức ưu tiên `Priority` (Urgent, High...).<br>• Giao việc xoay vòng `Assignment Rule`. | • **Ma trận SLA 2 chiều:** Gói VIP (30' phản hồi) vs Standard.<br>• **Skill-based Routing:** 3 bộ quy tắc gán việc theo ngành chuyên môn.<br>• **Custom Fields:** `custom_asset`, `custom_incident_time`, `custom_root_cause`, `custom_has_callback`.<br>• **Nút bấm 1-chạm Mobile (Client Script):** [Check-in], [Xuất linh kiện], [Hoàn thành ca]. |
| **Thiết bị & Bảo trì** | • Bảng `Asset` theo dõi tài sản.<br>• Lập lịch bảo trì `Asset Maintenance`.<br>• Nhật ký bảo trì `Asset Maintenance Log`. | • **Khai báo 5 máy công nghiệp** (Hitachi, Flexo, Daikin, Cummins, MSB) + 1 công cụ đo SKF.<br>• **Cách ly kế toán (Asset Isolation):** Tắt khấu hao `calculate_depreciation = 0`, gán cờ `custom_is_customer_equipment = 1`, gắn chủ sở hữu `custom_customer`.<br>• **Tem QR Code dán máy:** Tự động sinh mã QR để quét báo lỗi tức thời. |
| **Kho & Vật tư** | • Bảng `Item`, `Warehouse`.<br>• Phiếu xuất/nhập/chuyển kho `Stock Entry`.<br>• Quản lý tồn kho tức thời `Bin`. | • **Cây kho FSM:** Kho Trung tâm, 3 Kho Xe KTV (`Van Stock`), Kho thu hồi xác hỏng.<br>• **Khai báo 12 linh kiện** và thiết lập mức cảnh báo Reorder.<br>• **Phân loại thanh toán:** Thêm trường `custom_billing_type` (`Under Warranty` vs `Billable to Customer`). |
| **Nhân sự Kỹ thuật** | • Bảng `User`, `Employee`. | • Tạo 3 chuyên viên: Nguyễn Văn An (Cơ khí), Trần Đình Bình (Điện), Lê Hoàng Cường (HVAC). |

---

## PHẦN 2: BỨC TRANH DOMAIN & BẢN ĐỒ CHỨC NĂNG TỔNG THỂ (DOMAIN BLUEPRINT)

### 2.1. Domain của Dự Án Là Gì?
Dự án giải quyết bài toán nghiệp vụ trong lĩnh vực:  
👉 **MRO (Maintenance, Repair, and Overhaul) & FSM (Field Service Management)**  
*(Quản lý dịch vụ kỹ thuật hiện trường & Bảo trì, Sửa chữa, Đại tu thiết bị công nghiệp)*

Đơn vị triển khai giả định là **Công ty TNHH Dịch vụ Kỹ thuật & Bảo trì Công nghiệp Alpha (AIS)**, phục vụ 3 khách hàng công nghiệp lớn:
1. *Công ty CP Bao bì Tân Á:* Hợp đồng VIP — Dây chuyền in Flexo & Hệ thống khí nén trục vít.
2. *Xí nghiệp Dược Hải Nam:* Hợp đồng Standard — Hệ thống Chiller làm lạnh sâu & Máy phát điện dự phòng.
3. *Công ty Nhựa & Cơ khí Song Long:* Hợp đồng Standard — Tủ điện phân phối tổng MSB & Máy ép thủy lực.

### 2.2. Ba Trụ Cột Chức Năng Cốt Lõi

```
                       ┌────────────────────────────────────────────────────────┐
                       │   HỆ SINH THÁI FSM & MRO (SMART HELPDESK & MAINT.)     │
                       └──────────────────────────┬─────────────────────────────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         ▼                                        ▼                                        ▼
┌────────────────────────────────┐       ┌────────────────────────────────┐       ┌────────────────────────────────┐
│   TRỤ CỘT 1: HELPDESK & SLA    │       │    TRỤ CỘT 2: QUẢN LÝ THIẾT BỊ │       │  TRỤ CỘT 3: QUẢN TRỊ KHO VẬT TƯ│
│  (Service Desk & Dispatching)  │       │     & BẢO TRÌ ĐỊNH KỲ (CMMS)   │       │   (MRO Spare Parts & Inventory)│
├────────────────────────────────┤       ├────────────────────────────────┤       ├────────────────────────────────┤
│ 1. Tiếp nhận sự cố đa kênh     │       │ 1. Hồ sơ lý lịch máy móc       │       │ 1. Quản lý kho đa tầng:        │
│    (Portal, Hotline, QR Code)  │       │    (Asset Registry, Serial No) │       │    Kho tổng, Kho xe KTV,       │
│ 2. Ma trận cam kết SLA 2 chiều │       │ 2. Lập kế hoạch bảo dưỡng định │       │    Kho thu hồi xác linh kiện   │
│    (VIP vs Standard x Priority)│       │    kỳ (1 tháng, 3 tháng, 6 th.)│       │ 2. Xuất/Nhập/Điều chuyển kho:  │
│ 3. Điều phối kỹ thuật thông    │       │ 3. Nhật ký kiểm tra, hiệu chuẩn│       │    Chuyển kho xe, xuất cho vé  │
│    minh (Skill-based Routing)  │       │    dụng cụ đo lường chuyên dụng│ 3. Định mức tồn kho an toàn &  │
│ 4. Theo dõi chuỗi sự cố tái    │       │ 4. Chuyển đổi trạng thái:      │       │    Cảnh báo Reorder tự động    │
│    phát (Callback / Recall)    │       │    Từ bảo dưỡng phát hiện hỏng │ 4. Phân định tài chính vật tư: │
│                                │       │    sang tạo phiếu sửa chữa     │       │    Bảo hành vs Tính tiền khách │
└────────────────────────────────┘       └────────────────────────────────┘       └────────────────────────────────┘
```

---

## PHẦN 3: PHÂN TÍCH 8 NỖI ĐAU DOANH NGHIỆP THỰC TẾ (8 COMPREHENSIVE PAIN POINTS)

Khi một doanh nghiệp kỹ thuật chưa số hóa mà quản trị bằng Zalo, Excel, sổ tay, họ sẽ gặp phải 8 nỗi đau nghiêm trọng:

### Nhóm Nỗi Đau 1: Ở Trụ Cột Helpdesk & Dịch Vụ Khách Hàng
* **PP-01 (Trễ hạn cam kết SLA — Vi phạm hợp đồng):**
  * *Thực tế:* Khách hàng VIP nhà máy bao bì dừng máy 1 giờ thiệt hại hàng trăm triệu đồng. Báo sự cố qua điện thoại/Zalo làm trôi tin nhắn, Dispatcher quên việc, KTV đến trễ hạn $\rightarrow$ Bị phạt hợp đồng, khách dọa hủy dịch vụ.
  * *Hệ quả:* Mất uy tín doanh nghiệp, tổn thất tài chính.
* **PP-02 (Điều phối "mù" chuyên môn — Kỹ năng không khớp việc):**
  * *Thực tế:* Phân công theo kiểu bốc thăm ngẫu nhiên. Ca cháy chập tủ điện cao thế lại giao cho thợ cơ khí máy nén khí; ca nghẹt đường ống Chiller lạnh lại giao cho thợ điện. KTV đến nơi không biết sửa, loay hoay mất cả ngày $\rightarrow$ Kéo dài thời gian khắc phục sự cố (MTTR).
* **PP-03 (Mất dấu chuỗi sự cố tái phát — Callback / Recall):**
  * *Thực tế:* Máy sửa xong 3 ngày sau lại hỏng đúng lỗi cũ. Do không lưu vết, công ty coi đây là sự cố mới hoàn toàn, cử người khác đến làm lại từ đầu $\rightarrow$ Không đánh giá được tay nghề KTV làm ẩu lần trước, khách hàng bức xúc.

### Nhóm Nỗi Đau 2: Ở Trụ Cột Quản Lý Thiết Bị & Bảo Trì Định Kỳ (CMMS)
* **PP-04 (Quên lịch bảo trì ngăn ngừa — Preventive Maintenance):**
  * *Thực tế:* Mỗi máy có chu kỳ bảo dưỡng khác nhau (thay dầu 3 tháng, nạp gas 6 tháng). Theo dõi bằng sổ sách dẫn đến bỏ quên $\rightarrow$ Máy móc cạn dầu, bó kẹt trục vít, hỏng đột ngột giữa ca sản xuất. Chi phí sửa chữa sự cố đắt gấp 5 lần bảo dưỡng định kỳ.
* **PP-05 (Máy móc không có "Hồ sơ bệnh án" — TCO mờ mịt):**
  * *Thực tế:* Ban giám đốc không biết một năm qua chiếc máy in Flexo đã hỏng mấy lần, đã tốn bao nhiêu tiền phụ tùng $\rightarrow$ Không có số liệu để tư vấn khách hàng nên đại tu hay thay máy mới.
* **PP-06 (Rủi ro pháp lý & Thuế về Tài sản):**
  * *Thực tế:* Thiết bị công nghiệp thuộc quyền sở hữu của **khách hàng**. Nhưng nếu nhân viên nhập bừa vào phần mềm kế toán thì phần mềm sẽ tự trích khấu hao tài sản của người khác vào chi phí công ty mình $\rightarrow$ Vi phạm luật kế toán và báo cáo thuế sai sự thật.

### Nhóm Nỗi Đau 3: Ở Trụ Cột Quản Lý Kho & Vật Tư Kỹ Thuật (Inventory)
* **PP-07 (Thiếu linh kiện tại hiện trường — Lãng phí thời gian di chuyển Truck-roll):**
  * *Thực tế:* KTV chạy xe 40km đến nhà máy khách hàng, tháo máy ra mới biết thiếu lọc dầu. Lại phải chạy 40km về kho lấy đồ rồi quay lại $\rightarrow$ Lãng phí gấp đôi tiền xăng xe, công thợ, và cháy hạn cam kết SLA.
* **PP-08 (Thất thoát phụ tùng trên xe lưu động & Kho chạm đáy đột ngột):**
  * *Thực tế:* KTV mang linh kiện lên xe máy/bán tải đi sửa, cuối tháng thủ kho kiểm thấy hụt 10 cái lọc dầu mà không ai nhận trách nhiệm. Ban đêm máy hỏng cần đồ thay mới phát hiện kho đã hết sạch từ tuần trước (Stockout).
* **PP-09 (Nhập nhèm dòng tiền: "Ai trả tiền phụ tùng?"):**
  * *Thực tế:* Xuất 2 cái lọc dầu trị giá 1.300.000 VNĐ. Kế toán không biết khoản tiền này công ty AIS phải chịu lỗ vì máy trong hạn bảo hành, hay phải lập hóa đơn thu tiền công ty Tân Á vì công nhân của họ làm hỏng.

---

## PHẦN 4: BẢN PHÂN TÍCH ĐÁNH ĐỔI KIẾN TRÚC (ARCHITECTURE DECISION RECORDS & TRADE-OFFS)

Không có giải pháp nào là hoàn hảo tuyệt đối. Mọi quyết định kỹ thuật của dự án đều là một sự **lựa chọn có tính toán (Trade-off)**:

### Quyết định 1: Tận dụng DocType `Asset` Có Sẵn vs. Tự Viết DocType Mới `Customer Equipment`
* **Vấn đề giải quyết:** PP-05 (Hồ sơ bệnh án máy) & PP-06 (Rủi ro thuế tài sản).
* **Phương án đã chọn:** Dùng DocType `Asset` native của ERPNext, nhưng **cách ly hoàn toàn khỏi sổ cái kế toán**:
  * Đặt `calculate_depreciation = 0` (Khóa triệt để tính năng trích khấu hao).
  * Đặt `custom_is_customer_equipment = 1` để đánh dấu cờ máy khách hàng.
  * Thêm `custom_customer` (Link $\rightarrow$ Customer) để định danh chủ sở hữu pháp lý.
* **Các phương án thay thế:**
  * *Phương án B:* Tự code một DocType mới tinh tên là `Customer Equipment`.
  * *Phương án C:* Dùng DocType `Serial No` có sẵn.
* **Đánh đổi (Trade-off):**
  * ✅ **ĐƯỢC:** Tận dụng được **100% toàn bộ phân hệ `Asset Maintenance`** có sẵn của ERPNext (lập lịch bảo trì, tạo phiếu kiểm tra định kỳ, phân công đội bảo trì) mà không tốn công viết lại từ đầu.
  * ❌ **MẤT:** Tên gọi `Asset` trong ERPNext vốn dĩ dành cho tài sản nội bộ. Người dùng mới có thể bị nhầm lẫn nếu không đọc tài liệu hướng dẫn.
* **Lý do chọn:** Tiết kiệm hàng trăm giờ lập trình lại bánh xe lịch bảo dưỡng, trong khi việc khóa khấu hao đã loại trừ 100% rủi ro kế toán.

### Quyết định 2: Skill-Based Routing vs. Round Robin Mù vs. Thuật Toán Định Vị GPS
* **Vấn đề giải quyết:** PP-01 (Trễ hạn SLA) & PP-02 (Giao việc sai chuyên môn).
* **Phương án đã chọn:** Bổ sung trường `custom_asset_category` trên Issue (tự động lấy từ Asset) và thiết lập **3 Quy tắc Assignment Rules chuyên ngành riêng biệt**:
  * Máy nén khí, Máy in $\rightarrow$ Gán cho **Nguyễn Văn An** (Chuyên gia Cơ khí & Khí nén).
  * Tủ điện MSB, Máy phát $\rightarrow$ Gán cho **Trần Đình Bình** (Chuyên gia Điện & Tự động hóa).
  * Hệ thống Chiller $\rightarrow$ Gán cho **Lê Hoàng Cường** (Chuyên gia Nhiệt Lạnh HVAC).
* **Các phương án thay thế:**
  * *Phương án A:* Dùng Round Robin mặc định (chia xoay vòng mù theo số lượng).
  * *Phương án C:* Tự code giải thuật kết nối GPS tính quãng đường di chuyển và cân bằng tải động (Load balancing).
* **Đánh đổi (Trade-off):**
  * ✅ **ĐƯỢC:** 100% cấu hình trực quan trên giao diện ERPNext, trong suốt, dễ kiểm soát, không cần duy trì code backend phức tạp. Chấm dứt triệt để việc thợ cơ khí đi sửa tủ điện.
  * ❌ **MẤT:** Chưa tự động cân bằng tải nếu một ngày có quá nhiều máy nén khí hỏng cùng lúc (ông An có thể bị quá tải vé).
* **Lý do chọn:** Đối với doanh nghiệp dịch vụ kỹ thuật, **đúng chuyên môn (Skill-fit)** quan trọng hơn nhiều so với việc chia đều việc. Giao một việc quá tải cho đúng chuyên gia vẫn xử lý tốt hơn là giao cho người không biết gì đến làm hỏng thêm máy.

### Quyết định 3: Tem Dán QR Code & Web Mobile Form vs. Viết Native Mobile App (Flutter/React)
* **Vấn đề giải quyết:** PP-07 (Rào cản hiện trường của KTV và Quản đốc nhà máy).
* **Phương án đã chọn:** Tự động sinh **Tem mã QR Code dán trên vỏ máy**. Quét bằng camera điện thoại sẽ mở form tạo Ticket với mã máy và tên khách hàng điền sẵn 100%. Trên form Issue tích hợp bộ 3 nút bấm tác vụ nhanh (`Client Script`): `[Check-in]` $\rightarrow$ `[Xuất linh kiện]` $\rightarrow$ `[Hoàn thành]`.
* **Các phương án thay thế:**
  * *Phương án B:* Viết một ứng dụng di động riêng (Native App Flutter/React Native).
  * *Phương án C:* Sử dụng phiếu biên bản giấy truyền thống.
* **Đánh đổi (Trade-off):**
  * ✅ **ĐƯỢC:** Chi phí 0 đồng, không cần cài đặt app, bất kỳ điện thoại nào có camera (iPhone, Android, Zalo) đều quét được ngay. Tỷ lệ người dùng chấp nhận sử dụng cao gấp 5 lần.
  * ❌ **MẤT:** Cần kết nối Internet (Online only). Nếu nhà máy nằm ở tầng hầm mất sóng 4G thì không mở được link web.
* **Lý do chọn:** Rào cản chuyển đổi số lớn nhất tại nhà xưởng là người dùng ngại tải app mới. Một chiếc tem dán quét ngay là giải pháp thực tế nhất.

### Quyết định 4: Mô Hình Kho Xe Di Động (Van Stock) vs. Xuất Thẳng Từ Kho Trung Tâm
* **Vấn đề giải quyết:** PP-07 (Lãng phí truck-roll) & PP-08 (Thất thoát vật tư trên đường).
* **Phương án đã chọn:** Thiết lập cây kho đa tầng gồm `Kho Trung tâm` và các `Kho Xe KTV` (`Kho Xe - An`, `Kho Xe - Binh`...). Quy trình 2 chặng: Đầu tuần điều chuyển đồ lên xe (`Material Transfer`), khi đi sửa thì xuất từ kho xe vào máy (`Material Issue`).
* **Các phương án thay thế:**
  * *Phương án B:* Chỉ có 1 Kho Trung tâm, KTV cần gì thì bốc nấy, xuất thẳng từ kho tổng.
  * *Phương án C:* Tủ linh kiện ký gửi (Consignment Stock) tại nhà máy khách hàng.
* **Đánh đổi (Trade-off):**
  * ✅ **ĐƯỢC:** Trách nhiệm vật chất minh bạch 100%. Hàng chuyển lên xe nào thì KTV xe đó chịu trách nhiệm. Tăng tỷ lệ sửa dứt điểm lần đầu (FTFR) vì KTV luôn có sẵn đồ trên xe.
  * ❌ **MẤT:** Quy trình thêm 1 bước chứng từ (Transfer trước, Issue sau).
* **Lý do chọn:** Chặn đứng "lỗ hổng đen" thất thoát linh kiện lưu động — nguyên nhân lớn nhất làm hao hụt lợi nhuận của các công ty bảo trì.

### Quyết định 5: Phân Loại Chi Phí Ngay Trên Phiếu Xuất (`Billing Type`) vs. Tách Luồng Bán Hàng Riêng
* **Vấn đề giải quyết:** PP-09 (Nhập nhèm dòng tiền Bảo hành vs Tính phí khách hàng).
* **Phương án đã chọn:** Thêm trường `custom_billing_type` trên phiếu `Stock Entry` với 2 lựa chọn chính: `Under Warranty` (AIS chịu lỗ bảo hành) và `Billable to Customer` (Xuất hóa đơn đòi tiền khách).
* **Các phương án thay thế:**
  * *Phương án B:* Tách làm 2 quy trình: Nếu tính tiền thì bắt buộc phòng bán hàng tạo `Sales Order`, kế toán duyệt rồi mới cho xuất kho.
* **Đánh đổi (Trade-off):**
  * ✅ **ĐƯỢC:** KTV đang cứu máy lúc nửa đêm có thể xuất đồ sửa ngay lập tức để cứu tiến độ sản xuất của khách, không bị vỡ cam kết thời gian SLA.
  * ❌ **MẤT:** Phụ thuộc vào tính trung thực của người làm phiếu.
* **Lý do chọn:** Nguyên tắc số 1 của dịch vụ bảo trì khẩn cấp: **Cứu nhà máy trước, thủ tục giấy tờ giải quyết sau.**

---

### BẢNG TỔNG HỢP: MA TRẬN ĐÁNH ĐỔI KIẾN TRÚC (MASTER TRADE-OFF MATRIX)
| Quyết định Kiến trúc | Phương án Đã chọn | Phương án Thay thế | Cái ĐƯỢC lớn nhất | Cái MẤT (Đánh đổi) | Lý do then chốt để chọn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Quản lý Thiết bị** | Tận dụng `Asset` + khóa khấu hao | Tự tạo DocType `Customer Equipment` | Dùng được 100% module Bảo trì `Asset Maintenance` | Tên gọi `Asset` dễ gây nhầm với tài sản công ty | Tránh viết lại bánh xe lịch bảo dưỡng |
| **2. Phân công việc** | Skill-Based Assignment Rules | Round Robin ngẫu nhiên / Thuật toán GPS | Đúng chuyên môn 100%, cấu hình trực quan | Chưa cân bằng được tải việc tự động | Chuyên môn quan trọng hơn chia đều |
| **3. Thao tác KTV** | Tem QR Code + Web Mobile | Viết Native App (Flutter/React Native) | Chi phí 0đ, không cần cài app, ai cũng quét được | Bắt buộc phải có mạng Internet | Rào cản người dùng sử dụng là thấp nhất |
| **4. Quản lý Phụ tùng** | Kho Xe di động (Van Stock) | Xuất trực tiếp từ Kho trung tâm | Trách nhiệm vật chất KTV minh bạch, tăng FTFR | Thêm 1 bước chứng từ điều chuyển kho | Chặn đứng thất thoát vật tư trên đường |
| **5. Dòng tiền Chi phí** | Cờ `Billing Type` trên phiếu xuất | Tách luồng Bán hàng (Sales Order) | Cứu máy khách nhanh nhất, không trễ SLA | Phụ thuộc tính cẩn thận của người chọn loại | Ưu tiên thời gian phục hồi sản xuất |

---

## PHẦN 5: CẨM NANG THAO TÁC GIAO DIỆN ERPNEXT (CLICK-BY-CLICK UI WALKTHROUGH)

Bạn hãy mở trình duyệt tại `http://localhost:8080/desk` và thao tác theo 4 tour sau:

### Tour 1: Tiếp Nhận Sự Cố & Xem Phân Bổ Theo Chuyên Môn
1. Bấm phím tắt **`Ctrl + K`**, gõ: **`Issue List`** $\rightarrow$ Nhấn Enter.
2. Xóa chữ `Open` trên thanh lọc để thấy đủ 6 sự cố.
3. **Quan sát cột ngoài cùng bên phải (Minh chứng Skill-based Routing):**
   * `ISS-2026-00004` (Sự cố tủ điện MSB): Có vòng tròn **`TD`** $\rightarrow$ Đã tự động gán cho **Trần Đình Bình** (Chuyên gia Điện).
   * `ISS-2026-00001` (Máy nén khí Hitachi): Có vòng tròn **`NV`** $\rightarrow$ Đã tự động gán cho **Nguyễn Văn An** (Chuyên gia Cơ khí).
   * `ISS-2026-00005` (Chiller Daikin đông đá): Có vòng tròn **`LC`** $\rightarrow$ Đã tự động gán cho **Lê Hoàng Cường** (Chuyên gia Nhiệt Lạnh).
4. **Bấm vào xem chi tiết vé `ISS-2026-00002`:**
   * Góc trên bên phải: Thấy nút màu xanh **`[ Bắt đầu xử lý (Check-in) ]`**.
   * Bên cạnh: Nút **`[ Tác vụ hiện trường ]`** $\rightarrow$ chọn **`[ Xuất linh kiện sửa ]`**.
   * Nút màu xanh lá: **`[ Hoàn thành ca (Resolve) ]`** $\rightarrow$ Bấm vào sẽ hiện popup hỏi nguyên nhân gốc và nghiệm thu.

### Tour 2: Xem Tem QR Code & Cách Ly Kế Toán Trên Thiết Bị
1. Bấm **`Ctrl + K`**, gõ: **`Asset List`** $\rightarrow$ Nhấn Enter.
2. Bấm vào máy **`ACC-ASS-2026-00002`** (Máy nén khí Hitachi):
   * **Nhìn ngay đầu trang:** Thấy **Hình ảnh Tem Mã QR Code** với dòng chữ *"QUÉT ĐỂ BÁO LỖI THIẾT BỊ NÀY"*.
   * **Nhìn trường `Customer / Owner`:** Hiện rõ `Cong ty CP Bao bi Tan A`.
   * **Nhìn trường `Is Customer Equipment`:** Tích chọn `Yes` (Máy khách hàng).
   * **Kéo xuống mục `Depreciation` (Khấu hao):** Mục này hoàn toàn để trống/tắt, không tính một đồng khấu hao nào vào sổ sách AIS.

### Tour 3: Kiểm Tra Xuất Kho & Cảnh Báo Đặt Hàng Lại
1. Bấm **`Ctrl + K`**, gõ: **`Stock Entry List`** $\rightarrow$ Nhấn Enter.
2. Bấm vào phiếu **`MAT-STE-2026-00002`**:
   * Thấy xuất 2 cái lọc dầu `PART-FLT-OIL01` giá 1.300.000 VNĐ.
   * Trường `Billing Type`: Đang ghi rõ là **`Under Warranty`** (Bảo hành).
   * Trường `Technician`: Ghi rõ `an.nguyen@smarthelpdesk.local`.
3. Bấm **`Ctrl + K`**, gõ: **`Item List`** $\rightarrow$ Chọn lọc dầu `PART-FLT-OIL01`:
   * Số lượng thực tế trong kho: **2 cái**.
   * Ngưỡng an toàn (`Reorder Level`): **3 cái**.
   * Hệ thống báo động: Tồn kho đã rớt xuống dưới ngưỡng an toàn, cần mua thêm.

---

## PHẦN 6: ĐÀO SÂU TỐI ƯU HÓA HỆ THỐNG HIỆN TẠI (DEEP-DIVE OPTIMIZATION)

Nếu muốn tiếp tục đào sâu để nâng cao chất lượng đề tài:
1. **Đào sâu về SLA (Cảnh báo leo thang tiền vi phạm):**
   * Viết Server Script quét mỗi 15 phút. Nếu vé của khách VIP đã trôi qua 50% thời hạn (ví dụ 15 phút) mà KTV chưa bấm nút `[Check-in]` $\rightarrow$ Hệ thống tự động bắn cảnh báo đẩy lên màn hình Dispatcher để can thiệp kịp thời.
2. **Đào sâu về Quản lý Kho (Quy trình trả xác linh kiện cũ - Core Return):**
   * Bắt buộc KTV khi thay 2 lọc dầu mới phải mang 2 lọc dầu cũ nộp về kho `Kho Thu hoi Linh kien Hong - SBN`. Thủ kho kiểm tra xác cũ đạt yêu cầu mới cho phép đóng Ticket.
3. **Đào sâu về Độ tin cậy Máy móc (MTBF & MTTR):**
   * Tự động thống kê: Máy nén khí này trung bình chạy bao nhiêu giờ thì bị lỗi quá nhiệt một lần? Giúp khách hàng ra quyết định nên sửa chữa hay thay máy mới.

---

## PHẦN 7: LỘ TRÌNH MỞ RỘNG & SCALE QUY MÔ TƯƠNG LAI (FUTURE ROADMAP)

```
                               ┌────────────────────────────────────────────────────────┐
                               │           TƯƠNG LAI: SMART MAINTENANCE ECOSYSTEM       │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
         ┌─────────────────────────┬──────────────────────┴───────────────┬─────────────────────────┐
         ▼                         ▼                                     ▼                         ▼
┌─────────────────┐       ┌─────────────────┐                   ┌─────────────────┐       ┌─────────────────┐
│ 1. AI RAG AGENT │       │ 2. IoT SENSORS  │                   │ 3. MOBILE PWA   │       │ 4. AUTO BILLING │
│ Chatbot tra cứu │       │ Cảm biến rung/  │                   │ KTV quét mã     │       │ Tự kết xuất hóa │
│ cẩm nang sửa    │       │ nhiệt tự báo lỗi│                   │ offline ngoài   │       │ đơn định kỳ     │
│ máy, gọi tool   │       │ qua giao thức   │                   │ hiện trường     │       │ theo hợp đồng   │
│ ERPNext kiểm kho│       │ MQTT / Webhook  │                   │ không có mạng   │       │ dịch vụ         │
└─────────────────┘       └─────────────────┘                   └─────────────────┘       └─────────────────┘
```

1. **Tích hợp Chatbot RAG AI Agent (Định hướng Cuối kỳ):**
   * Mô hình LLM kết hợp Vector Database chứa toàn bộ tài liệu kỹ thuật (Manual PDF) của máy móc.
   * Khi KTV hỏi: *"Máy nén khí báo lỗi E-04 thì sửa thế nào và kho còn đồ không?"*
   * $\rightarrow$ AI đọc lỗi từ Manual, sau đó gọi Function Calling/MCP vào ERPNext kiểm tra tồn kho `PART-FLT-OIL01` và trả lời ngay trên màn hình.
2. **Tích hợp Cảm biến IoT / SCADA (Bảo trì dự đoán - Predictive Maintenance):**
   * Gắn cảm biến nhiệt độ/độ rung lên máy. Khi nhiệt độ vượt quá 95°C trong 3 phút $\rightarrow$ Cảm biến tự động bắn API vào ERPNext tạo một Issue khẩn cấp trước khi máy phát nổ.
3. **Mở rộng Doanh nghiệp Đa chi nhánh (Multi-Site Scaling):**
   * Mở rộng phục vụ hàng trăm nhà máy từ Bắc vào Nam, phân cấp quản lý theo từng vùng miền nhưng vẫn gom chung dữ liệu kế toán tài chính về trụ sở chính.
