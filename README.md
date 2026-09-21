# ERP Smart HelpDesk & Maintenance Management

Hệ thống quản lý HelpDesk và Bảo trì bảo dưỡng thiết bị (Maintenance Management) tích hợp trên nền tảng **ERPNext** (hỗ trợ cả môi trường **Frappe Cloud** và **Docker Local**).

---

## 📌 Nội dung & Mục tiêu dự án

- **Master Data & Cấu hình**: Thiết lập Công ty, Kho hàng (Warehouses), Phân loại sự cố (Issue Type), Ưu tiên (Priority), Phụ tùng linh kiện với ngưỡng đặt hàng lại tự động (Auto-reorder) và Hồ sơ thiết bị công nghiệp (Fixed Assets).
- **Service Level Agreement (SLA)**: Quy định ma trận phản hồi (First Response) và xử lý sự cố (Resolution Time) 2 chiều theo phân hạng VIP / Standard.
- **Phân công tự động (Round Robin)**: Phân bổ sự cố xoay vòng công bằng cho đội ngũ kỹ thuật viên bảo trì.
- **Kịch bản vận hành & Kiểm chứng (End-to-End)**:
  - Ghi nhận và xử lý yêu cầu sự cố & kế hoạch bảo dưỡng định kỳ thiết bị.
  - Xuất kho linh kiện thay thế sửa chữa (`Stock Entry - Material Issue`) gắn định danh Issue, Asset, Kỹ thuật viên.
  - Tự động cập nhật nhật ký bảo trì (`Asset Maintenance Log`).
  - Kiểm chứng điều kiện kích hoạt cảnh báo tồn kho an toàn khi phụ tùng dưới ngưỡng.

---

## 📂 Cấu trúc Thư mục Dự án Chuẩn Doanh nghiệp

```text
Project_SmartHelpDesk_Mainternance/
├── .env                              # File cấu hình môi trường hiện hành (Local / Cloud)
├── .env.example                      # File mẫu cấu hình biến môi trường
├── .gitignore                        # Cấu hình bỏ qua các file nhạy cảm và tạm thời
├── README.md                         # Tài liệu giới thiệu & hướng dẫn tổng quan dự án
├── requirements.txt                  # Danh mục phụ thuộc Python
├── run_pipeline.py                   # [KHUYẾN NGHỊ] Script chạy toàn bộ pipeline (01 -> 05) với 1 lệnh
│
├── docs/                             # TÀI LIỆU DỰ ÁN & BÁO CÁO
│   ├── reports/
│   │   ├── midterm_report.md         # Báo cáo giữa kỳ chi tiết toàn diện
│   │   └── plan_midterm.md           # Kế hoạch & lộ trình triển khai
│   ├── specifications/
│   │   ├── master_data.md            # Đặc tả chi tiết dữ liệu nền tảng
│   │   └── verification_matrix.md    # Ma trận kiểm chứng kịch bản & ca kiểm thử
│   └── assets/
│       └── screenshots/              # Album ảnh chụp màn hình minh chứng thực tế
│
├── scripts/                          # MÃ NGUỒN TỰ ĐỘNG HÓA HỆ THỐNG
│   ├── core/
│   │   └── frappe_client.py          # Thư viện giao tiếp REST API (tự động nhận diện .env)
│   ├── setup/
│   │   ├── 01_setup_master_data.py   # [Bước 1] Khởi tạo Công ty, Kho, Item, Asset
│   │   ├── 02_setup_technicians.py   # [Bước 2] Khởi tạo User, Employee, Team, Round Robin
│   │   ├── 03_setup_custom_fields.py # [Bước 3] Thêm Custom Fields cho FSM & SLA
│   │   └── 04_setup_sla_and_plans.py # [Bước 4] Thiết lập SLA 2 chiều & Kế hoạch bảo trì
│   ├── scenarios/
│   │   └── 05_execute_scenarios.py   # [Bước 5] Thực thi 6 kịch bản kiểm thử End-to-End
│   └── prototypes/
│       └── 06_server_script_prototypes.py # Mã nguyên mẫu Server Scripts nâng cao
│
├── data/                             # DỮ LIỆU KIỂM CHỨNG ĐẦU RA
│   └── verification_evidence.json    # Dữ liệu JSON ghi nhận bằng chứng kiểm thử
│
└── docker/                           # TIỆN ÍCH QUẢN LÝ ERPNEXT LOCAL
    ├── README.md                     # Hướng dẫn chi tiết môi trường Docker
    ├── start.bat                     # 1-Click khởi động container ERPNext
    └── stop.bat                      # 1-Click dừng container để tiết kiệm RAM
```

---

## 🚀 Hướng dẫn Cài đặt & Vận hành

### 1. Cấu hình Môi trường Kết nối
Tạo file `.env` từ file mẫu:
```bash
cp .env.example .env
```

#### Tùy chọn A: Kết nối tới ERPNext Docker Local
```env
FRAPPE_BASE_URL=http://localhost:8080
FRAPPE_API_KEY=f76b087b4d0fd45
FRAPPE_API_SECRET=e00918ed98d7fd8
```

#### Tùy chọn B: Kết nối tới Frappe Cloud
```env
FRAPPE_BASE_URL=https://smarthelpdesk23mainternace.s.frappe.cloud
FRAPPE_API_KEY=your_cloud_api_key
FRAPPE_API_SECRET=your_cloud_api_secret
```

---

### 2. Chạy Toàn bộ Hệ thống (Khuyến nghị)
Chạy script điều phối duy nhất để tự động kiểm tra kết nối và khởi tạo từ bước 01 đến 05:

```bash
python run_pipeline.py
```

---

### 3. Hoặc Chạy Từng Bước Thủ công
Nếu muốn debug hoặc thiết lập từng thành phần:

```bash
# Bước 1: Dữ liệu nền tảng
python scripts/setup/01_setup_master_data.py

# Bước 2: Kỹ thuật viên & Luật gán việc
python scripts/setup/02_setup_technicians.py

# Bước 3: Custom Fields
python scripts/setup/03_setup_custom_fields.py

# Bước 4: Ma trận SLA & Kế hoạch bảo trì
python scripts/setup/04_setup_sla_and_plans.py

# Bước 5: Kịch bản kiểm chứng thực tế
python scripts/scenarios/05_execute_scenarios.py
```
