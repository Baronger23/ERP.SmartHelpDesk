KẾ HOẠCH GIỮA KỲ HOÀN CHỈNH — Smart Helpdesk & Maintenance trên ERPNext

(Tổng hợp sau toàn bộ quá trình phản biện — đây là bản chốt để bạn triển khai)

0. Business Scenario (làm trước tiên, trước khi đụng vào ERPNext)

Chốt một domain cụ thể, nhất quán — không dùng thiết bị ngẫu nhiên:

Doanh nghiệp giả định: Công ty dịch vụ sửa chữa & bảo trì thiết bị công nghiệp

Dataset nhỏ nhưng liên kết chặt với nhau:

3 Customer, 3 Supplier, 3 Technician (Agent)
5 Asset (có Asset Category rõ ràng, ví dụ: Industrial Printer, HVAC, Compressor, Electrical Panel, Generator)
10–15 Item (linh kiện thay thế)
3 Maintenance Plan (định kỳ cho 3/5 Asset)
5–10 HD Ticket (có cả Repair và Preventive Maintenance)
5–10 Stock Transaction (nhập/xuất)

Nguyên tắc bắt buộc: mỗi Asset → Ticket → Maintenance → Parts phải nối được với nhau thành một câu chuyện nghiệp vụ liền mạch — vì đây chính là dataset cuối kỳ sẽ tái sử dụng cho AI/RAG, không làm lại từ đầu.

PHASE 1 — Environment & Version Pinning
Cài trên Frappe Cloud (ưu tiên) hoặc Docker — không tự host bằng bench trên VM trần trừ khi môn học bắt buộc.
Chốt version ngay từ đầu và không upgrade giữa chừng (tránh feature đổi hành vi giữa các tuần làm báo cáo).
Ghi vào báo cáo bảng "Environment Specification": ERPNext version, Frappe version, Helpdesk version, Database, Deployment, OS.
Nguyên tắc xuyên suốt cả đồ án: Documented capability ≠ Verified capability — mọi tính năng dùng trong báo cáo phải được tự tay kiểm chứng trên instance thật, không chỉ trích tài liệu.
PHASE 2 — Master Data

Company → Customer → Supplier → Employee/User → Item Group → Item → Warehouse → Asset Category → Asset (gán Category, Serial No, Purchase Date, Location, Department).

PHASE 3 — Helpdesk
HD Team, Agent, gán vào Team.
Ticket Type (Repair, Preventive Maintenance, Technical Consultation, Inspection, Installation) — tách biệt hoàn toàn khỏi Priority (Low/Medium/High/Urgent).
SLA: tạo tối thiểu 2 bộ (Standard Customer / VIP Customer) để demo khác biệt thời gian phản hồi-xử lý.
Assignment Rule: Round Robin/Load Balancing — tự kiểm tra trên đúng version đang dùng xem Agent Availability có hoạt động như tài liệu mô tả không.
Ticket lifecycle mở rộng, đây là nghiệp vụ chính chứ không chỉ demo trạng thái:
NEW → TRIAGED → ASSIGNED → IN PROGRESS
                              │
                    ┌── Need Parts ──┐
                    ↓                ↓
            WAITING FOR PARTS → PARTS READY
                    │                │
                    └────────┬───────┘
                              ↓
                        RESOLVED → CLOSED
Kênh tiếp nhận: Portal là kênh demo chính (native, dễ làm). Email làm thêm nếu còn thời gian. Phone/Zalo không native — xử lý bằng "Manual Ticket Creation" (nhân viên helpdesk tạo ticket hộ khi khách gọi/nhắn Zalo) — đưa vào mô hình As-Is/To-Be, không bỏ qua vì đây là kênh thực tế phổ biến nhất ở doanh nghiệp Việt Nam.
PHASE 4 — Maintenance

Phân biệt rõ hai luồng (đây là điểm ăn điểm quan trọng vì tên đề tài là "Sửa chữa - Bảo trì"):

Preventive Maintenance	Corrective/Repair
Theo lịch (Asset Maintenance → Periodicity)	Thiết bị hỏng đột xuất
→ Maintenance Log tự sinh	→ HD Ticket → Technician xử lý
PHASE 5 — Inventory

Purchase Receipt → Warehouse → Material Request → Stock Entry (Issue/Receipt) → Reorder Level.

Lưu ý quan trọng: Auto Reorder chạy qua scheduled job, không real-time. Khi demo, hoặc trigger job thủ công, hoặc trình bày bằng lời: "Auto Reorder không phải cơ chế event-driven real-time mà thực hiện qua scheduled process; nhóm chủ động trigger job để chứng minh kết quả trong môi trường demo."

PHASE 6 — Cross-module Integration (Customization)

Đây là phần bắt buộc dùng Custom Field — không có sẵn native trong Helpdesk chuẩn (đã xác minh: chưa có link Ticket–Asset mặc định, cộng đồng Frappe còn đang đề xuất tính năng này):

HD Ticket ↔ Asset (custom link)
Asset Maintenance Log ↔ HD Ticket (custom link — trường hợp bảo trì phát hiện lỗi → sinh ticket sửa chữa)
Stock Entry ↔ HD Ticket, ↔ Asset, ↔ Technician (custom fields: custom_hd_ticket, custom_asset, custom_technician)
PHASE 7 — Testing & Verification Matrix

Không chỉ chụp màn hình — dùng bảng kiểm chứng:

ID	Requirement	Feature	Test	Expected	Result
HD-01	Tạo ticket	HD Ticket	Customer tạo qua Portal	Ticket + SLA + Agent gán tự động	PASS
HD-02	SLA	SLA	Ticket Priority=High, Customer VIP	Response 30'	PASS
HD-03	Auto-assign	Assignment Rule	3 agent, 4 ticket liên tiếp	Round robin đúng thứ tự	PASS
MT-01	Bảo trì định kỳ	Asset Maintenance	Chu kỳ tháng	Maintenance Log tự sinh	PASS
INV-01	Xuất kho	Stock Entry	Issue 2 MOSFET	Stock giảm đúng, gắn Ticket	PASS
INV-02	Reorder	Auto Reorder	Stock < Reorder Level	Material Request (trigger job thủ công)	PASS*
PHASE 8 — Fit-Gap Analysis + Data Classification

Fit-Gap (nghiệp vụ):

Requirement	ERPNext hỗ trợ	Cách triển khai
Ticket, SLA, Assignment	✅	Native (Helpdesk)
Preventive Maintenance	✅	Native (Asset Maintenance)
Inventory, Reorder	✅	Native (Stock)
Ticket ↔ Asset/Stock	⚠️	Custom Field
Kênh Phone/Zalo	❌	Manual creation / Integration layer
AI Diagnosis, RAG	❌	Cuối kỳ

Data Classification (bảng cầu nối sang cuối kỳ):

Data	Loại	Dùng cho AI cuối kỳ
Customer, Asset, Item, Stock	Structured	ERPNext API / structured retrieval
Ticket, Maintenance Log	Structured + Text	Historical case retrieval
Manual, Circuit Diagram, Troubleshooting Guide	Unstructured	Vector DB / RAG

Kết luận nối giữa kỳ → cuối kỳ, viết nguyên văn dạng này trong báo cáo: "Dữ liệu chuẩn hóa trong ERPNext ở giữa kỳ trở thành nguồn dữ liệu nghiệp vụ có cấu trúc; tài liệu kỹ thuật không cấu trúc được xây thành Knowledge Base riêng. Hệ thống AI cuối kỳ sẽ kết hợp hai nguồn qua kiến trúc hybrid retrieval, trong đó ERPNext là source of truth cho tồn kho/nghiệp vụ, Knowledge Base là source of truth cho kiến thức kỹ thuật, còn LLM chỉ đóng vai trò reasoning layer chứ không tự quyết định số liệu tồn kho."

PHASE 9 — Midterm Report

Cấu trúc: Business Requirements → As-Is Process → To-Be Process với ERPNext → Environment Spec → Configuration → DocType Relationship (không gọi ERD) → Verification Matrix → Fit-Gap Analysis → Data Classification → Limitations → Foundation for AI/RAG.

Ghi chú kiến trúc cuối kỳ (để chuẩn bị tinh thần, không làm ngay giữa kỳ)

Khi tới cuối kỳ, kiến trúc RAG nên có Intent Router phân loại câu hỏi trước khi truy vấn, thay vì luôn tìm cả hai nguồn:

User Query → Intent Router
   ├─ Inventory Query      → ERPNext API (structured)
   ├─ Technical Knowledge  → Vector Search (unstructured)
   └─ Hybrid (vd: "lỗi E05 cần linh kiện gì, kho còn không?")
         → RAG xác định linh kiện cần thiết
         → ERPNext xác minh tồn kho thực tế
         → LLM tổng hợp câu trả lời cuối

Nguyên tắc cốt lõi: LLM không bao giờ tự "đoán" số liệu tồn kho — mọi con số tồn kho phải lấy từ ERPNext, LLM chỉ suy luận linh kiện cần dùng dựa trên RAG.