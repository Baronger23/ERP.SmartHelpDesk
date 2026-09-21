# BỘ MASTER DATA CHUẨN — DỰ ÁN SMART HELPDESK & MAINTENANCE
**Hệ thống:** ERPNext v15 (Frappe Cloud)  
**Mã dự án:** `smarthelpdesk23mainternace`  
**Doanh nghiệp giả định:** Công ty TNHH Dịch vụ Kỹ thuật & Bảo trì Công nghiệp Alpha (Alpha Industrial Services - AIS)

---

## 1. Doanh nghiệp & Cơ cấu tổ chức
* **Company:** Alpha Industrial Services (Viết tắt: `AIS`)
* **Default Currency:** `VND`
* **Country:** Vietnam
* **Kho bãi (Warehouses):**
  * `Kho Linh kiện Trung tâm - AIS` (Kho chính lưu trữ phụ tùng nhập về)
  * `Kho Xe Kỹ thuật Di động - AIS` (Kho phụ trên xe cơ động của kỹ thuật viên khi đi bảo trì)

---

## 2. Người dùng & Phân quyền kỹ thuật (Technicians / Agents)

| Họ và tên | Username / Email | Role Profile | Chuyên môn kỹ thuật | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **Nguyễn Văn An** | `an.nguyen@ais.vn` | Helpdesk Agent / Maintenance User | Cơ khí - Khí nén & Máy in công nghiệp | Kỹ thuật viên chính (Tier 2) |
| **Trần Đình Bình** | `binh.tran@ais.vn` | Helpdesk Agent / Maintenance User | Điện công nghiệp & Tủ điều khiển PLC | Kỹ thuật viên chính (Tier 2) |
| **Lê Hoàng Cường** | `cuong.le@ais.vn` | Helpdesk Agent / Maintenance User | Nhiệt - Lạnh công nghiệp & Máy phát điện | Kỹ thuật viên chính (Tier 2) |
| **Phạm Thu Hà** | `ha.pham@ais.vn` | Helpdesk Manager | Điều phối dịch vụ (Dispatcher / Triager) | Trưởng nhóm tiếp nhận & phân công |

---

## 3. Khách hàng B2B (Customers)

| Mã KH | Tên Khách hàng | Nhóm KH | Phân hạng SLA | Địa chỉ lắp đặt máy | Liên hệ chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CUST-TANA` | Công ty CP Bao bì Tân Á | Commercial | **VIP Customer** | KCN Hòa Khánh, Đà Nẵng | Anh Hùng (GĐ Nhà máy) |
| `CUST-HAINAM` | Xí nghiệp Dược Hải Nam | Commercial | **Standard** | KCN Điện Nam - Điện Ngọc, Quảng Nam | Chị Lan (Quản lý thiết bị) |
| `CUST-SONGLONG` | Công ty Nhựa & Cơ khí Song Long | Commercial | **Standard** | KCN Liên Chiểu, Đà Nẵng | Anh Dũng (Trưởng ca kỹ thuật) |

---

## 4. Nhà cung cấp linh kiện (Suppliers)

| Mã NCC | Tên Nhà cung cấp | Nhóm cung cấp | Mặt hàng cung cấp chính |
| :--- | :--- | :--- | :--- |
| `SUPP-KIMLONG` | Công ty TNHH Thiết bị Khí nén Kim Long | Spare Parts | Lọc gió, Lọc dầu, Dầu làm mát máy nén |
| `SUPP-MINHPHAT` | Công ty TNHH Thiết bị Điện Minh Phát | Electrical Parts | Contactor, Relay nhiệt, Cảm biến, Aptomat |
| `SUPP-TIENDAT` | Nhà phân phối Vật tư Kỹ thuật Tiến Đạt | Industrial Hardware | Bơm dầu, Dây curoa, Vòng bi, Đầu phun |

---

## 5. Danh mục & 5 Tài sản quản lý (Assets)

Tất cả 5 thiết bị này đều được bảo dưỡng hoặc sửa chữa theo hợp đồng dịch vụ ký với 3 khách hàng trên.

| Mã Tài sản | Tên Thiết bị | Asset Category | Khách hàng sở hữu | Serial No | Vị trí đặt | Kỹ thuật phụ trách |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AST-PRN-01` | Máy in phun công nghiệp Flexo 6 màu | Industrial Printing | Công ty CP Bao bì Tân Á | `FLX-2023-8891` | Xưởng In 1 | Nguyễn Văn An |
| `AST-CMP-02` | Máy nén khí trục vít Hitachi 75kW | Compressor | Công ty CP Bao bì Tân Á | `HTC-OSA-75-01` | Phòng Máy nén khí | Nguyễn Văn An |
| `AST-CHL-03` | Hệ thống Chiller giải nhiệt nước Daikin 100RT | HVAC & Cooling | Xí nghiệp Dược Hải Nam | `DK-CW-100-99` | Khu Kỹ thuật mái | Lê Hoàng Cường |
| `AST-GEN-04` | Máy phát điện dự phòng Cummins 250kVA | Generator | Xí nghiệp Dược Hải Nam | `CUM-C250-772` | Nhà xe trạm điện | Lê Hoàng Cường |
| `AST-PNL-05` | Tủ điện phân phối tổng MSB 1200A | Electrical Panel | Công ty Nhựa Song Long | `MSB-SL-1200A` | Phòng Điện trung tâm | Trần Đình Bình |

---

## 6. Danh mục 12 Linh kiện & Vật tư thay thế (Items)

* **Item Group chính:** `Linh kiện Sửa chữa - Bảo trì` (Maintainable Spare Parts)
* Mọi Item đều bật: `Is Stock Item = 1`, `Allow Alternative Item = 0`.

| Mã Item | Tên Linh kiện | ĐVT | Giá nhập ước tính | Min Reorder Level | Dùng cho Asset nào |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `PART-FLT-OIL01` | Lọc dầu máy nén khí Hitachi (Oil Filter) | Cái | 650.000 đ | 3 | `AST-CMP-02` |
| `PART-FLT-AIR01` | Lọc gió máy nén khí trục vít 75kW | Cái | 850.000 đ | 2 | `AST-CMP-02` |
| `PART-OIL-COOL01` | Dầu làm mát tổng hợp New Alpha Screw (Thùng 20L) | Thùng | 3.200.000 đ | 2 | `AST-CMP-02` |
| `PART-NOZ-FLX01` | Đầu phun mực in công nghiệp Piezo 1020 | Cái | 8.500.000 đ | 1 | `AST-PRN-01` |
| `PART-BLT-TIM01` | Dây curoa răng truyền động bản 50mm | Sợi | 420.000 đ | 4 | `AST-PRN-01` |
| `PART-VAL-EXP01` | Van tiết lưu điện tử Chiller Danfoss ETS50 | Cái | 4.600.000 đ | 1 | `AST-CHL-03` |
| `PART-SEN-TEMP01` | Cảm biến nhiệt độ PT100 công nghiệp (-50 đến 200°C) | Cái | 380.000 đ | 5 | `AST-CHL-03`, `AST-CMP-02` |
| `PART-FLT-DSL01` | Lọc nhiên liệu Diesel máy phát điện Cummins | Cái | 550.000 đ | 3 | `AST-GEN-04` |
| `PART-AVR-CUM01` | Bo mạch điều tốc tự động AVR Stamford SX460 | Cái | 2.100.000 đ | 1 | `AST-GEN-04` |
| `PART-CNT-150A` | Khởi động từ Contactor Schneider LC1D150 150A | Cái | 3.800.000 đ | 2 | `AST-PNL-05` |
| `PART-RLY-THM01` | Rơ-le nhiệt bảo vệ quá tải Schneider LRD3353 | Cái | 1.150.000 đ | 3 | `AST-PNL-05` |
| `PART-FUS-500A` | Cầu chì hạ thế gG 500A 690V | Cái | 280.000 đ | 6 | `AST-PNL-05` |

---

## 7. Kế hoạch bảo trì định kỳ (3 Maintenance Plans - Phase 4)

1. **Bảo trì định kỳ Máy nén khí (`AST-CMP-02`):**
   * *Chu kỳ:* 1 tháng / lần (Monthly)
   * *Công việc:* Vệ sinh lọc gió, kiểm tra mức dầu, xả nước bẫy ngưng tụ, đo dòng động cơ.
   * *Người phụ trách:* Nguyễn Văn An.
2. **Bảo dưỡng Chiller giải nhiệt nước (`AST-CHL-03`):**
   * *Chu kỳ:* 3 tháng / lần (Quarterly)
   * *Công việc:* Tẩy cặn bình ngưng, đo áp suất gas R134a, kiểm tra độ ồn máy nén lạnh, siết tiếp điểm động lực.
   * *Người phụ trách:* Lê Hoàng Cường.
3. **Kiểm định & bảo dưỡng Tủ điện MSB (`AST-PNL-05`):**
   * *Chu kỳ:* 6 tháng / lần (Half-Yearly)
   * *Công việc:* Dùng camera nhiệt quét điểm tiếp xúc thanh cái (busbar), test ngắt ACB, vệ sinh bụi bằng khí nén khô.
   * *Người phụ trách:* Trần Đình Bình.

---

## 8. Kịch bản 5 Helpdesk Tickets nối mạch nghiệp vụ (Phase 3 & 7)

* **Ticket #1 (VIP - Sửa chữa đột xuất - Cần xuất kho):**
  * *Khách hàng:* Công ty CP Bao bì Tân Á (VIP)
  * *Thiết bị:* `AST-CMP-02` (Máy nén khí trục vít)
  * *Tiêu đề:* "Máy nén khí báo lỗi quá nhiệt E-04 và tự ngắt ca làm việc"
  * *Độ ưu tiên:* Urgent (SLA cam kết phản hồi 30 phút, xử lý 4 giờ).
  * *Luồng xử lý:* Kỹ thuật viên Nguyễn Văn An kiểm tra -> nghẹt lọc dầu làm giảm lưu lượng làm mát -> Chuyển trạng thái `WAITING FOR PARTS` -> Xuất kho 1 cái `PART-FLT-OIL01` và 1 thùng `PART-OIL-COOL01` -> Trạng thái `PARTS READY` -> Thay thế xong -> `RESOLVED` -> `CLOSED`.
* **Ticket #2 (Standard - Kiểm tra định kỳ theo yêu cầu):**
  * *Khách hàng:* Xí nghiệp Dược Hải Nam
  * *Thiết bị:* `AST-GEN-04` (Máy phát điện Cummins)
  * *Tiêu đề:* "Yêu cầu chạy thử tải và thay lọc dầu chuẩn bị mùa mưa bão"
  * *Độ ưu tiên:* Medium (SLA 4h / 24h).
  * *Xử lý:* Xuất kho 1 cái `PART-FLT-DSL01`, hoàn thành kiểm tra tải.
* **Ticket #3 (VIP - Hỏng đột xuất):**
  * *Khách hàng:* Công ty CP Bao bì Tân Á
  * *Thiết bị:* `AST-PRN-01` (Máy in công nghiệp Flexo)
  * *Tiêu đề:* "Màu số 3 in ra bị sọc ngang, nghi nghẹt đầu phun"
  * *Độ ưu tiên:* High.
  * *Xử lý:* Vệ sinh đầu phun bằng dung môi chuyên dụng, căn chỉnh lại, không cần thay mới linh kiện.
* **Ticket #4 (Standard - Sự cố điện):**
  * *Khách hàng:* Công ty Nhựa Song Long
  * *Thiết bị:* `AST-PNL-05` (Tủ điện MSB)
  * *Tiêu đề:* "Mùi khét tại nhánh bơm ép số 2, CB nhánh bị nhảy"
  * *Độ ưu tiên:* High.
  * *Xử lý:* Thay 1 Contactor `PART-CNT-150A` do tiếp điểm bị rỗ hồ quang.
* **Ticket #5 (Ticket sinh từ Bảo trì định kỳ - Predictive/Preventive):**
  * *Khách hàng:* Xí nghiệp Dược Hải Nam
  * *Thiết bị:* `AST-CHL-03` (Hệ thống Chiller)
  * *Tiêu đề:* "Phát hiện chênh lệch nhiệt độ sensor PT100 trong kỳ bảo dưỡng Chiller tháng 9"
  * *Nguồn gốc:* Sinh trực tiếp từ Maintenance Log của Asset Maintenance.
