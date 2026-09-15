# ERP Smart HelpDesk & Maintenance Management

Hệ thống quản lý HelpDesk và Bảo trì bảo dưỡng thiết bị (Maintenance Management) tích hợp trên nền tảng ERPNext / Frappe Cloud.

## 📌 Nội dung dự án

- **Master Data & Cấu hình**: Thiết lập công ty, phòng ban, phân loại sự cố (Issue Type), ưu tiên (Priority), vật tư linh kiện và định mức tồn kho tối thiểu (Auto-reorder).
- **Service Level Agreement (SLA)**: Quy định thời gian phản hồi (First Response) và xử lý sự cố (Resolution Time) theo phân hạng VIP / Standard.
- **Phân công tự động (Round Robin)**: Kỹ thuật viên bảo trì được tự động gán việc luân phiên công bằng.
- **Kịch bản vận hành & Kiểm chứng**:
  - Ghi nhận yêu cầu & bảo dưỡng định kỳ/đột xuất cho thiết bị.
  - Xuất kho linh kiện thay thế (`Stock Entry - Material Issue`).
  - Cập nhật nhật ký bảo trì (`Asset Maintenance Log`).
  - Cảnh báo tự động đặt hàng khi linh kiện dưới ngưỡng an toàn.

## 📂 Cấu trúc thư mục

```text
├── scripts/                          # Bộ script tự động hóa cấu hình và kiểm chứng
│   ├── 01_setup_master_data.py       # Khởi tạo dữ liệu nền tảng
│   ├── 02_setup_technicians_and_rules.py # Cấu hình kỹ thuật viên & Round Robin
│   ├── 03_setup_custom_fields.py     # Thêm Custom Fields cho Desk/Issue (bao gồm custom_incident_time)
│   ├── 04_setup_sla_and_plans.py     # Cấu hình Ma trận SLA 2 chiều & kế hoạch bảo trì
│   ├── 05_execute_scenarios.py       # Chạy các kịch bản kiểm chứng end-to-end
│   ├── 06_server_script_prototypes.py# Mã nguyên mẫu Server Script (Skill-based routing & Absence)
│   └── frappe_client.py              # Thư viện giao tiếp REST API Frappe Cloud
├── screenshots/                      # Ảnh chụp màn hình minh chứng các luồng hoạt động
├── midterm_report.md                 # Báo cáo chi tiết giữa kỳ
├── Plan_midterm.md                   # Kế hoạch thực hiện
├── master_data.md                    # Tài liệu dữ liệu tổng thể
├── verification_matrix.md            # Ma trận kiểm chứng kịch bản
├── verification_evidence.json        # Dữ liệu bằng chứng kiểm thử
├── .env.example                      # File mẫu cấu hình biến môi trường
└── README.md                         # Tài liệu hướng dẫn dự án
```

## 🚀 Hướng dẫn cài đặt & Chạy script

### 1. Cấu hình môi trường

Tạo file `.env` từ file mẫu `.env.example`:

```bash
cp .env.example .env
```

Cập nhật thông tin kết nối vào `.env`:

```env
FRAPPE_BASE_URL=https://your-site.frappe.cloud
FRAPPE_API_KEY=your_api_key_here
FRAPPE_API_SECRET=your_api_secret_here
```

### 2. Cài đặt thư viện

- **Python**: Sử dụng Python 3.8+ (chỉ sử dụng standard library `urllib`, không cần cài thêm gói ngoài).

### 3. Chạy các bước thiết lập & kiểm chứng

```bash
python scripts/01_setup_master_data.py
python scripts/02_setup_technicians_and_rules.py
python scripts/03_setup_custom_fields.py
python scripts/04_setup_sla_and_plans.py
python scripts/05_execute_scenarios.py
```
