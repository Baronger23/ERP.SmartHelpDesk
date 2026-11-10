# KẾ HOẠCH THỰC HIỆN — ĐƯA CODE LÊN DEVELOP → DỰNG BENCH WSL → REFACTOR & CÀI LẠI ERPNEXT TRÊN BENCH → REFACTOR VÒNG 2

*Dự án SmartHelpDesk (repo `Baronger23/ERP.SmartHelpDesk`). Kế hoạch lập ngày 10/11/2026, dựa trên số đo thật trên laptop của Bao tại thời điểm lập (không dựa trên trí nhớ). Chưa bước nào được thực thi — chờ Bao duyệt kế hoạch này mới bắt đầu.*

---

## 0. HIỆN TRẠNG ĐO ĐƯỢC (10/11/2026) VÀ NGUYÊN TẮC XUYÊN SUỐT

| Hạng mục | Số đo thật | Ý nghĩa với kế hoạch |
|---|---|---|
| Nhánh hiện tại | `develop`, ngang bằng `origin/develop` (không ahead/behind) | Mọi thứ mới đều đang nằm ngoài git |
| Commit gần nhất | `049ee89 feat: deployment architecture` | Từ đó đến nay chưa có commit nào chứa code SHD |
| Chưa commit (modified) | `.gitignore`, `README.md`, `run_pipeline.py`; xóa `docs/design/fix/data-architecture.png` | Có vẻ file ảnh kiến trúc đã được chuyển vị trí (có bản mới ở `docs/design/data-architecture.png`, cũng chưa commit) — phải rà soát ở Giai đoạn 0 |
| Chưa commit (untracked) | `apps/` (toàn bộ app SHD), `docker/compose.business.yml`, `scripts/setup/install_business_app.py`, `scripts/tests/`, `data/business_validation.json` + `business_ui_validation.json`, `docs/implementation/`, `docs/presentations/`, 3 file nghiên cứu + 2 thư mục diagram mới, và `output/` | Lớp SHD vẫn chỉ tồn tại trên một máy duy nhất — rủi ro số một, xử lý đầu tiên |
| `output/` | ~50MB sản phẩm build slide | **Không commit** — phải chặn bằng `.gitignore` trước khi commit hàng loạt |
| Ổ đĩa | C còn trống **19,9GB**, E còn **23,7GB** (đã cải thiện nhiều so với 8,6GB ngày 28/10) | Đạt ngưỡng an toàn ≥15GB trên C để dựng bench trong WSL |
| WSL | WSL2 + Ubuntu 24.04 đang chạy, Python 3.12.3 sẵn, chưa có bench, chưa có Node | Dựng bench là cài thêm, không phải cài lại từ đầu |
| Hệ đang chạy | Docker (`frappe_docker`, localhost:8080) | Là hệ chính thức cho tới khi bench chứng minh được — không đụng vào |

**Bốn nguyên tắc:**

1. **Không phá hệ đang chạy.** Docker giữ nguyên vai trò hệ chính cho đến hết Giai đoạn 2; bench là môi trường song song. Mọi sự cố ở bench đều không ảnh hưởng việc demo/báo cáo bằng Docker.
2. **Mỗi giai đoạn có điểm kiểm chứng và đường lui.** Không giai đoạn nào bắt đầu khi giai đoạn trước chưa đạt điểm kiểm chứng.
3. **Refactor chỉ diễn ra trên nhánh riêng** (`feat/bench-standard-app`), chỉ merge vào `develop` khi bộ test xanh; `develop` luôn ở trạng thái chạy được.
4. **Không commit rác:** `output/`, `__pycache__`, `*.egg-info`, `.env` bị chặn bởi `.gitignore` trước mọi thao tác commit.

---

## GIAI ĐOẠN 0 — CHỐT AN TOÀN VÀ ĐẨY CODE HIỆN TẠI LÊN NHÁNH DEVELOP

*Mục đích: biến toàn bộ lớp SHD từ "file trên một laptop" thành "code trên GitHub", để mọi refactor phía sau đều có điểm quay lui. Ước lượng: nửa buổi.*

| Bước | Việc cụ thể | Kiểm chứng |
|---|---|---|
| 0.1 | Rà soát diff của 3 file modified và cặp file ảnh kiến trúc (bản bị xóa ở `docs/design/fix/`, bản mới ở `docs/design/`) — xác nhận đây là di chuyển vị trí có chủ đích, không phải mất file | Đọc diff thật, liệt kê trước khi commit |
| 0.2 | Bổ sung `.gitignore`: thêm `output/` (và rà soát lại toàn bộ danh sách chặn) | `git status` không còn hiện `output/` |
| 0.3 | Commit theo 6 lát sạch (không gộp một cục): (1) `feat(app)`: toàn bộ `apps/`; (2) `feat(infra)`: `docker/compose.business.yml` + `scripts/setup/install_business_app.py` + `scripts/tests/`; (3) `docs(implementation)`: `docs/implementation/` + `docs/presentations/`; (4) `docs(research)`: 3 file nghiên cứu + 2 thư mục diagram trong `docs/`; (5) `chore`: `.gitignore`, `README.md`, `run_pipeline.py`, hai file `data/*.json`; (6) `docs`: di chuyển file ảnh kiến trúc | `git log` đọc được như một câu chuyện; mỗi commit tự đứng vững |
| 0.4 | Push: thêm remote phụ `origin-ssh` = `git@github.com:Baronger23/ERP.SmartHelpDesk.git` và push bằng khóa ed25519 đã có sẵn trên laptop (khóa "Bao laptop acer" đã đăng ký trên chính tài khoản Baronger23 — cùng cơ chế `origin-ssh` đang chạy tốt ở repo PBL6); remote HTTPS `origin` giữ nguyên không đụng | `git ls-remote origin-ssh develop` khớp hash local; mở trang GitHub đối chiếu thấy đủ file |
| 0.5 | Gắn tag `pre-bench-baseline` tại commit cuối của giai đoạn này | Tag xuất hiện trên GitHub — đây là mốc quay lui chính thức trước refactor |
| 0.6 | Kiểm chứng tính đầy đủ: clone tươi repo về một thư mục tạm và đối chiếu cây file (đặc biệt `apps/`) với bản trên laptop, phòng trường hợp `.gitignore` nuốt nhầm file cần thiết | Số file khớp; xóa thư mục clone thử sau khi xong |

*Người thực hiện: Muse qua SSH (commit + push). Bao không phải thao tác gì, trừ tình huống dự phòng: nếu push SSH gặp sự cố ngoài dự kiến, Bao chạy một lệnh `git push` từ PowerShell của mình.*

**ĐIỂM KIỂM CHỨNG G0:** GitHub nhánh `develop` chứa đầy đủ lớp SHD + tài liệu nghiên cứu; tag `pre-bench-baseline` tồn tại.

---

## GIAI ĐOẠN 1 — REFACTOR VÒNG 1: ĐƯA APP VỀ CHUẨN FRAPPE ĐỂ CÀI ĐƯỢC BẰNG BENCH

*Mục đích: hiện nay app khai báo 28 DocType bằng code trong `schema.py` và cài qua installer tự chế (`install_business_app.py` chạy bench qua Docker exec) — lệch thông lệ Frappe. Vòng 1 đưa app về đúng dạng chuẩn mà `bench install-app` hiểu được. Chỉ đổi "cách đóng gói", tuyệt đối không đổi hành vi nghiệp vụ. Làm trên nhánh `feat/bench-standard-app`. Ước lượng: 1–2 buổi.*

| Bước | Việc cụ thể | Kiểm chứng |
|---|---|---|
| 1.1 | Viết script chuyển đổi tự động từ `schema.py` sang cây chuẩn `smart_helpdesk/smart_helpdesk/doctype/<ten>/` (file JSON + controller Python) cho cả 28 DocType — không gõ tay để tránh sai sót | Script đối chiếu chéo từng DocType/từng field giữa JSON sinh ra và `schema.py`: phải khớp 100% mới đi tiếp |
| 1.2 | Tách phần việc của `install.py` thành cơ chế chuẩn: 8 role, Workspace, Access Grant mẫu... chuyển sang fixtures/hooks chuẩn của Frappe; `after_install` chỉ giữ lại phần thật sự không có cơ chế chuẩn thay thế (nếu còn) và phải ghi lý do | Cài app lên một site trống bằng đúng `bench install-app` + `migrate`, không cần `install_business_app.py` |
| 1.3 | Giữ nguyên 100% lõi nghiệp vụ: 40 lệnh, `sla.py`, `api.execute`, idempotency, SHD Event — vòng này không sửa một dòng logic nào | Bộ test hiện hữu là lưới an toàn (bước 1.4) |
| 1.4 | Chuyển bộ test (21 test tích hợp + 5 test lịch SLA) sang chạy bằng cơ chế test của bench trên site kiểm thử, song song giữ harness cũ để so sánh kết quả giữa môi trường Docker và Bench | Kết quả hai môi trường khớp nhau: 21 + 5 test đều đạt, trên chính app đã refactor |

**ĐIỂM KIỂM CHỨNG G1:** app dạng chuẩn cài sạch lên site trống bằng lệnh bench chuẩn; hành vi không đổi (test xanh, kết quả khớp môi trường cũ).

---

## GIAI ĐOẠN 2 — DỰNG BENCH TRONG WSL VÀ CÀI ERPNEXT TỪ ĐẦU THEO CÁCH CỦA THẦY

*Mục đích: thực hành đúng quy trình chuẩn đã học: bench init → get-app → new-site → install-app → bench start. Điều kiện tiên quyết về ổ đĩa đã đạt (C trống 19,9GB). Ước lượng: 1 buổi (bước tải source ở 2.3 là lâu nhất, khoảng 15–30 phút tùy mạng).*

| Bước | Việc cụ thể | Kiểm chứng |
|---|---|---|
| 2.1 | Trong Ubuntu (WSL): cài MariaDB server, Redis, Node 20 + yarn, wkhtmltopdf và các thư viện hệ thống; cài `frappe-bench` bằng pip cho user hiện tại | `bench --version`, `node --version` trả kết quả đúng |
| 2.2 | Cấu hình MariaDB theo yêu cầu Frappe: charset utf8mb4, tài khoản root dùng được cho bench tạo site | Bench tạo được database thử mà không lỗi quyền |
| 2.3 | `bench init frappe-bench --frappe-branch version-16` (tải source Frappe v16 — cùng họ phiên bản với bản Docker đang chạy v16.33.1/16.34.2), sau đó `bench get-app erpnext --branch version-16` | Mở thư mục bench bằng VS Code thấy đúng cấu trúc `apps/frappe`, `apps/erpnext` như thầy demo |
| 2.4 | `bench new-site shd.localhost` → `bench --site shd.localhost install-app erpnext` → `bench start` | Mở `localhost:8000`, đăng nhập Administrator, Desk hiện, mở thử vài module ERPNext (Item, Customer, Sales Invoice) |
| 2.5 | Đưa app đã refactor (Giai đoạn 1) vào bench bằng `get-app` từ bản local/GitHub → `bench --site shd.localhost install-app smart_helpdesk` → `bench --site shd.localhost migrate` | 28 DocType SHD xuất hiện trong site; Workspace Smart Helpdesk hiện đủ 10 lối tắt |
| 2.6 | Nghiệm thu trên bench: chạy bộ test (21 + 5) và thực hiện tay một ca sửa chữa trọn vòng (tiếp nhận → giữ vật tư → tiêu hao → nghiệm thu → hóa đơn) | Test xanh; ca thử chảy đúng như trên Docker |

*Đường lui: nếu Giai đoạn 2 vướng lỗi khó quá nửa buổi, dừng lại, ghi lỗi vào file này, Docker vẫn là hệ chính — không ảnh hưởng tiến độ môn học. Bench dựng dở có thể xóa làm lại từ 2.3 mà không mất gì (code đã an toàn trên GitHub từ Giai đoạn 0).*

**ĐIỂM KIỂM CHỨNG G2:** một site ERPNext + SmartHelpDesk chạy hoàn toàn trên bench WSL, cài từ đầu bằng lệnh chuẩn, test xanh.

---

## GIAI ĐOẠN 3 — REFACTOR VÒNG 2: DỌN DẸP KHI BENCH ĐÃ LÀ "NHÀ MỚI"

*Mục đích: sau khi bench chạy được, dọn những gì vòng 1 chưa đụng: lớp legacy, installer Docker, chất lượng code và tài liệu. Ước lượng: 1 buổi.*

| Bước | Việc cụ thể | Kiểm chứng |
|---|---|---|
| 3.1 | Xử lý dứt điểm lớp script legacy: chuyển `scripts/setup/01–06`, `scripts/scenarios/`, `scripts/reports/` vào thư mục `legacy/` kèm README ghi rõ trạng thái "demo giữa kỳ, đóng băng" — lịch sử vẫn còn cho thầy xem, nhưng không ai nhầm là hệ thống hiện hành | Cây thư mục đọc một cái hiểu ngay lớp nào là hiện hành |
| 3.2 | Quyết định số phận Docker: đề xuất **giữ Docker làm môi trường phụ** nhưng cập nhật để dùng app dạng chuẩn mới (bỏ phụ thuộc `install_business_app.py` nếu cơ chế chuẩn đã thay thế được), vì demo/CI cũ đang dựa vào Docker | Docker vẫn dựng được hệ thống từ app mới |
| 3.3 | Nâng chất lượng code trong app: docstring/type hints cho các lệnh nghiệp vụ, tách file nếu có file quá lớn, chạy lint theo chuẩn Frappe | Lint sạch; test vẫn xanh sau dọn dẹp |
| 3.4 | Viết lại README cài đặt theo đường bench là chính (Docker là phụ), và bổ sung kết quả thực hành bench vào hai tài liệu nghiên cứu (tổng quan + kế hoạch nghiên cứu) để buổi trình bày có bằng chứng "đã tự cài theo quy trình chuẩn" | Người lạ đọc README làm theo được |
| 3.5 | Merge `feat/bench-standard-app` → `develop`, push qua `origin-ssh`, gắn tag `bench-migration-done` | GitHub phản ánh trạng thái cuối |

**ĐIỂM KIỂM CHỨNG CUỐI:** clone tươi từ GitHub → làm đúng theo README trên một bench trống → site chạy, test xanh. Đây là kiểm chứng "người khác cài lại được", tiêu chuẩn cao nhất của cả kế hoạch.

---

## RỦI RO CHÍNH VÀ CÁCH GIẢM THIỂU

| Rủi ro | Giảm thiểu |
|---|---|
| Đầy ổ đĩa giữa chừng khi bench tải source + node_modules | Đã đạt ngưỡng (C: 19,9GB); theo dõi dung lượng sau mỗi bước lớn; nếu sát ngưỡng thì dọn thêm hoặc chuyển hướng sang ổ E trước khi tiếp tục |
| MariaDB trên Ubuntu dùng cơ chế đăng nhập root khác mặc định Frappe mong đợi | Bước 2.2 xử lý riêng và kiểm chứng bằng site thử trước khi làm thật |
| Lẫn Node của Windows với Node trong WSL | Mọi lệnh bench chỉ chạy bên trong Ubuntu; Node 20 cài riêng trong WSL ở bước 2.1 |
| Refactor vòng 1 làm lệch hành vi âm thầm | Script đối chiếu JSON ↔ schema.py khớp 100% + lưới test chạy trên cả hai môi trường và so kết quả |
| Push qua SSH bị chặn như từng gặp ở repo khác | Dùng đúng cơ chế `origin-ssh` đã kiểm chứng chạy được với cùng tài khoản GitHub; dự phòng cuối cùng là Bao push từ PowerShell |
| Bench tốn thời gian hơn dự kiến, ảnh hưởng lịch trình bày | Thứ tự giai đoạn đảm bảo giá trị tăng dần: chỉ cần xong Giai đoạn 0 là rủi ro lớn nhất (mất code) đã hết; các giai đoạn sau dừng ở đâu cũng không mất gì đã đạt |

**Tổng ước lượng: 3–4 buổi làm việc**, trong đó Giai đoạn 0 nên làm ngay vì nó khép rủi ro mất code đang tồn tại từ 28/10.

---

## CÁC QUYẾT ĐỊNH CẦN BAO DUYỆT KHI DUYỆT KẾ HOẠCH

| Mã | Quyết định | Đề xuất của Muse |
|---|---|---|
| D1 | Chuyển 28 DocType từ khai báo bằng code (`schema.py`) sang JSON chuẩn của Frappe | **Có** — đây là cốt lõi của "làm theo cách chuẩn"; script chuyển đổi + đối chiếu tự động giữ an toàn |
| D2 | Tên site trên bench | `shd.localhost` (khớp thói quen đặt tên site kiểm thử hiện có) |
| D3 | Số phận lớp script legacy ở Giai đoạn 3 | Chuyển vào thư mục `legacy/` trong repo (không xóa, không để lẫn) |
| D4 | Số phận môi trường Docker sau khi bench xong | Giữ làm môi trường phụ, cập nhật theo app chuẩn mới |
| D5 | Thứ tự các giai đoạn | Cố định 0 → 1 → 2 → 3: phải có code an toàn trên GitHub trước (G0), app phải về dạng chuẩn trước khi bench cài được nó (G1 → G2). Nếu thời gian eo hẹp, dừng sau G0 vẫn đã khép được rủi ro lớn nhất |

*Duyệt kế hoạch này đồng nghĩa: Muse bắt đầu Giai đoạn 0 ngay (rà soát diff → commit 6 lát → push origin-ssh → gắn tag), rồi báo cáo điểm kiểm chứng G0 trước khi sang Giai đoạn 1.*
