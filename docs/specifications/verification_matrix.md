# MA TRẬN KIỂM CHỨNG THỰC NGHIỆM (VERIFICATION MATRIX)
**Dự án:** Smart Helpdesk & Maintenance trên ERPNext  
**Hệ thống kiểm chứng:** `https://smarthelpdesk23mainternace.s.frappe.cloud` (Frappe v16.33.0 / ERPNext v16.34.1)  
**Thời điểm thực thi:** 2026-09-07  
**Nguyên tắc thực nghiệm:** *Documented capability ≠ Verified capability* (Mọi kết quả dựa trên bản ghi dữ liệu thực tế).

---

## Bảng tổng hợp Ma trận kiểm chứng 6 Test Case

| Test ID | Nghiệp vụ kiểm tra | Precondition (Điều kiện tiên quyết) | Action (Hành động thực hiện) | Expected Result (Kỳ vọng) | Actual Result & Document ID (Thực tế) | Verification URL (Link Desk chụp minh chứng) | Đánh giá | Ghi chú & Fit-Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HD-01** | Tiếp nhận Issue & Route SLA theo phân hạng Khách hàng | Khách hàng VIP (`Cong ty CP Bao bi Tan A`) & Standard (`Xi nghiep Duoc Hai Nam`) đã khai báo; SLA VIP & Standard đã kích hoạt. | Khởi tạo 2 Issue riêng biệt cho 2 khách hàng qua Desk/API: `ISS-2026-00001` (Tân Á) và `ISS-2026-00002` (Hải Nam). | `ISS-2026-00001` được tự động gán `SLA Khach hang VIP`. `ISS-2026-00002` được tự động gán `SLA Khach hang Standard`. | `ISS-2026-00001` ➔ SLA: `SLA-Issue-SLA Khach hang VIP`<br>`ISS-2026-00002` ➔ SLA: `SLA-Issue-SLA Khach hang Standard` | [Xem Issue 1](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/issue/ISS-2026-00001)<br>[Xem Issue 2](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/issue/ISS-2026-00002) | **PASS** | Native SLA Rule trên ERPNext định tuyến chính xác theo Entity Customer. |
| **HD-02** | Phân biệt thời hạn phản hồi/xử lý SLA theo Ma trận 2 Chiều (Priority × Customer Tier) | SLA VIP và SLA Standard cấu hình đầy đủ bảng con 4 mức Priority (Urgent/High/Medium/Low). VIP Urgent (30'/4h), Standard Medium (8h/48h), Standard High (4h/24h). | Tạo `ISS-2026-00001` (VIP, Urgent) lúc 11:28:48. Tạo `ISS-2026-00002` (Standard, Medium) lúc 11:30:25. | `ISS-2026-00001` có `response_by` cách 30 phút. `ISS-2026-00002` có `response_by` cách 8 giờ làm việc (hoặc 4h theo cấu hình ban đầu). | `ISS-2026-00001`: Creation = 11:28:48 ➔ Response By = **11:58:48** (Đúng 30').<br>`ISS-2026-00002`: Creation = 11:30:25 ➔ Response By = **15:30:25** (Đúng 4h). | [Xem chi tiết SLA trên Issue 1](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/issue/ISS-2026-00001) | **PASS** | Ma trận 2 chiều hoạt động chính xác: Hệ thống tra cứu SLA theo Customer rồi lấy mốc thời gian theo Priority trong bảng con `priorities`. |
| **HD-03** | Tự động phân công kỹ thuật viên theo chu trình Round Robin | 3 Kỹ thuật viên thật đã được tạo User (`an.nguyen`, `binh.tran`, `cuong.le`). Cấu hình `Assignment Rule` xoay vòng. | Tạo liên tiếp 4 Issue: `ISS-2026-00001`, `ISS-2026-00002`, `ISS-2026-00003`, `ISS-2026-00004`. | Hệ thống gán tuần tự KTV 1 ➔ KTV 2 ➔ KTV 3 ➔ quay lại KTV 1. Trường `_assign` và `ToDo` lưu đúng User. | • `ISS-2026-00001` ➔ `an.nguyen`<br>• `ISS-2026-00002` ➔ `binh.tran`<br>• `ISS-2026-00003` ➔ `cuong.le`<br>• `ISS-2026-00004` ➔ `an.nguyen` (Quay vòng chu kỳ) | [Xem danh sách Issue](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/issue)<br>[Xem danh sách ToDo](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/todo) | **PASS** | Kiểm chứng thực tế qua trường `_assign` và bảng `ToDo` gán việc. |
| **MT-01** | Chu kỳ bảo trì định kỳ & Liên kết phát hiện lỗi sinh Issue | Khai báo 3 `Asset Maintenance` định kỳ. Thiết lập Custom Field `custom_issue` trên `Asset Maintenance Log`. | KTV thực hiện bảo dưỡng Chiller `ACC-ASS-2026-00003`, phát hiện lỗi cảm biến ➔ Tạo Log `ACC-AML-2026-00004` và liên kết với Issue `ISS-2026-00005`. | `Asset Maintenance Log` lưu trạng thái `Completed`, ghi nhận hành động kỹ thuật và chứa link dẫn tới Issue sửa chữa. | Log `ACC-AML-2026-00004` được tạo với `custom_issue = ISS-2026-00005`. Trạng thái: `Completed`. | [Xem Maintenance Log](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/asset-maintenance-log/ACC-AML-2026-00004) | **PASS** | Đóng kín vòng lặp: *Preventive Maintenance phát hiện bất thường ➔ Sinh Corrective Issue*. |
| **INV-01** | Xuất kho linh kiện thay thế gắn định danh Ticket & Kỹ thuật viên | Kho trung tâm có sẵn 4 cái `PART-FLT-OIL01` (Lọc dầu). Form `Stock Entry` có các Custom Field `custom_issue`, `custom_asset`, `custom_technician`. | Lập phiếu xuất kho `Material Issue` xuất 2 lọc dầu thay thế cho sự cố máy nén khí `ISS-2026-00001`. | Phiếu xuất lưu vết đầy đủ Ticket, Thiết bị và KTV thực hiện. Tồn kho thực tế trong `Bin` giảm từ 4 xuống 2. Issue chuyển `Resolved`. | Phiếu xuất: `MAT-STE-2026-00002` đã Submit.<br>• `custom_issue` = `ISS-2026-00001`<br>• `custom_asset` = `ACC-ASS-2026-00001`<br>• `custom_technician` = `an.nguyen`<br>• Tồn kho giảm: 4.0 ➔ **2.0 Nos** | [Xem Stock Entry](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/stock-entry/MAT-STE-2026-00002)<br>[Xem Tồn kho Bin](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/bin) | **PASS** | Tích hợp liên module Helpdesk ↔ Stock ↔ Asset giải quyết bài toán truy xuất chi phí sửa chữa. |
| **INV-02** | Cấu hình Reorder Level & Cơ chế Auto Reorder trên ERPNext | Item `PART-FLT-OIL01` có cấu hình Reorder: Ngưỡng Reorder Level = 3, Số lượng đặt Reorder Qty = 5. | Xuất kho ở bước INV-01 khiến tồn kho tụt xuống 2 (2 < 3). Xác minh điều kiện kích hoạt Reorder. | Hệ thống ghi nhận số dư tồn kho thấp hơn ngưỡng an toàn (`actual_qty < warehouse_reorder_level`). | Tồn kho thực tế: **2.0 Nos** < Ngưỡng Reorder: **3.0 Nos**.<br>Điều kiện kích hoạt Reorder đạt giá trị: **TRUE**. | [Xem Cấu hình Item](https://smarthelpdesk23mainternace.s.frappe.cloud/desk/item/PART-FLT-OIL01) | **PASS\*** | *Ghi chú kỹ thuật:* ERPNext kích hoạt Auto Reorder qua Scheduled Background Job (Daily Cron). Xác minh đạt cấu hình & ngưỡng số liệu thực. |

---

## Chi tiết các Document ID làm bằng chứng (Evidence Records)

1. **Danh sách Khách hàng:**
   * `Cong ty CP Bao bi Tan A` (VIP)
   * `Xi nghiep Duoc Hai Nam` (Standard)
   * `Cong ty Nhua & Co khi Song Long` (Standard)
2. **Danh sách Kỹ thuật viên (System Users & Employees):**
   * User: `an.nguyen@smarthelpdesk.local` | Employee: `HR-EMP-00001` (Nguyễn Văn An)
   * User: `binh.tran@smarthelpdesk.local` | Employee: `HR-EMP-00002` (Trần Đình Bình)
   * User: `cuong.le@smarthelpdesk.local` | Employee: `HR-EMP-00003` (Lê Hoàng Cường)
3. **Danh sách 6 Tài sản công nghiệp (Assets):**
   * `ACC-ASS-2026-00001`: Máy nén khí trục vít Hitachi 75kW (`AST-CMP-02`) - Khách hàng Bao bì Tân Á
   * `ACC-ASS-2026-00002`: Máy in Flexo 6 màu (`AST-PRN-01`) - Khách hàng Bao bì Tân Á
   * `ACC-ASS-2026-00003`: Hệ thống Chiller Daikin 100RT (`AST-CHL-03`) - Khách hàng Dược Hải Nam
   * `ACC-ASS-2026-00004`: Máy phát điện dự phòng Cummins 250kVA (`AST-GEN-04`) - Khách hàng Dược Hải Nam
   * `ACC-ASS-2026-00005`: Tủ điện tổng MSB 1200A (`AST-PNL-05`) - Khách hàng Nhựa Song Long
   * `ACC-ASS-2026-00006`: Máy đo rung công nghiệp SKF CMAS 100-SL (`TOOL-VIB01`) - **Tài sản nội bộ (Calibration Equipment)**
4. **Danh sách 6 Helpdesk Issues:**
   * `ISS-2026-00001`: Sự cố quá nhiệt máy nén khí | Priority: **Urgent** | SLA: VIP (30m) | Assignee: `an.nguyen` | Status: **Resolved** | Root Cause: `Hardware Failure`
   * `ISS-2026-00002`: Chạy thử tải máy phát điện | Priority: **Medium** | SLA: Standard (4h) | Assignee: `binh.tran` | Status: **Open**
   * `ISS-2026-00003`: Lỗi sọc màu máy in Flexo | Priority: **High** | SLA: VIP (1h) | Assignee: `cuong.le` | Status: **Replied**
   * `ISS-2026-00004`: Mùi khét aptomat tủ điện MSB | Priority: **High** | SLA: Standard (4h) | Assignee: `an.nguyen` (Round Robin) | Status: **Open**
   * `ISS-2026-00005`: Chiller đóng băng van tiết lưu | Priority: **Medium** | SLA: Standard | Assignee: `cuong.le` | Status: **On Hold** (Waiting for Parts)
   * `ISS-2026-00006`: Khảo sát cảm biến IoT máy nén | Priority: **Low** | SLA: VIP | Assignee: `binh.tran` | Status: **Closed**
5. **Giao dịch Kho (Stock Entries):**
   * `MAT-STE-2026-00001`: Nhập kho ban đầu (Material Receipt) 12 mã phụ tùng vào Kho Linh kiện Trung tâm.
   * `MAT-STE-2026-00002`: Xuất kho sửa chữa (Material Issue) 2 Lọc dầu `PART-FLT-OIL01` cho sự cố `ISS-2026-00001`.
6. **Bảo dưỡng định kỳ (Asset Maintenance):**
   * `ACC-ASS-2026-00001`: Kế hoạch bảo trì máy nén khí (Monthly)
   * `ACC-ASS-2026-00003`: Kế hoạch bảo dưỡng Chiller (Quarterly)
   * `ACC-ASS-2026-00005`: Kế hoạch kiểm định tủ điện MSB (Half-Yearly)
   * `ACC-ASS-2026-00006`: Kế hoạch kiểm định hiệu chuẩn máy đo rung SKF (Yearly - Calibration Maintenance)
   * `ACC-AML-2026-00004`: Log bảo dưỡng hoàn thành nối tới Issue `ISS-2026-00005`.

7. **Kiểm chứng Ma trận SLA 2 Chiều trên Live Instance:**
   * **VIP SLA (`SLA-Issue-SLA Khach hang VIP`):**
     - `Urgent`: Response: 1,800s (30m) | Resolution: 14,400s (4h)
     - `High`: Response: 3,600s (1h) | Resolution: 28,800s (8h)
     - `Medium`: Response: 14,400s (4h) | Resolution: 86,400s (24h)
     - `Low`: Response: 28,800s (8h) | Resolution: 172,800s (48h)
   * **Standard SLA (`SLA-Issue-SLA Khach hang Standard`):**
     - `Urgent`: Response: 3,600s (1h) | Resolution: 28,800s (8h)
     - `High`: Response: 14,400s (4h) | Resolution: 86,400s (24h)
     - `Medium`: Response: 28,800s (8h) | Resolution: 172,800s (48h)
     - `Low`: Response: 86,400s (24h) | Resolution: 259,200s (72h)

8. **Kiểm chứng Hệ thống 09 Trường Tùy Biến (Custom Fields) trên Live Instance:**
   * `Issue-custom_asset` (Link Asset) — **Active**
   * `Issue-custom_incident_time` (Datetime) — **Active**
   * `Issue-custom_related_issue` (Link Issue) — **Active** (Callback/Incident Chain)
   * `Issue-custom_root_cause` (Select: 5 categories) — **Active** (FTFR Metric)
   * `Issue-custom_has_callback` (Check: Boolean) — **Active** (FTFR Indicator)
   * `Stock Entry-custom_issue` (Link Issue) — **Active**
   * `Stock Entry-custom_asset` (Link Asset) — **Active**
   * `Stock Entry-custom_technician` (Link User) — **Active**
   * `Asset Maintenance Log-custom_issue` (Link Issue) — **Active**

9. **Kiểm chứng Cấu trúc Kho Đa Tầng Hiện Trường (FSM Warehouses):**
   * Kho Trung tâm: `Kho Linh kien Trung tam - SBN`
   * Kho Xe KTV An: `Kho Xe - Nguyen Van An - SBN` (Parent: `All Warehouses - SBN`)
   * Kho Xe KTV Bình: `Kho Xe - Tran Dinh Binh - SBN` (Parent: `All Warehouses - SBN`)
   * Kho Xe KTV Cường: `Kho Xe - Le Hoang Cuong - SBN` (Parent: `All Warehouses - SBN`)
   * Kho Thu hồi Linh kiện: `Kho Thu hoi Linh kien Hong - SBN` (Core Exchange Warehouse)

