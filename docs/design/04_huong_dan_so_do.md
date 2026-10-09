# Hướng dẫn sơ đồ, công cụ và cách trình bày

## 1. Công cụ đã kiểm tra và sử dụng

Plugin Figma có khả năng tạo diagram FigJam trong ChatGPT/Codex, nhưng kết nối chưa được xác nhận trong phiên làm việc này. Đã đề xuất cài/kết nối; không tuyên bố đã dùng FigJam khi chưa có công cụ hoạt động. [Figma mô tả tích hợp ChatGPT](https://www.figma.com/blog/turn-your-chatgpt-brainstorms-into-figjam-diagrams/).

Plugin Canva đang có kết nối và đã dùng để tạo [bản đồ năng lực doanh nghiệp](https://canva.link/bucs6cajm4rbjqc). Đã kiểm tra nội dung, sửa nhãn tiếng Việt và lưu sau khi người dùng xem preview, phê duyệt. Bản này là bố cục trình bày được sinh từ brief; bản nguồn kỹ thuật trong repo là nơi đối chiếu đầy đủ quan hệ. Thay đổi tiếp theo vẫn cần kiểm tra nội dung trước khi dùng làm slide chính thức.

Bản Canva là capability map phiên bản 2 đã duyệt. Kiến trúc Agent Harness v3 được cập nhật trong SVG/Draw.io/Markdown cục bộ; không coi bản Canva cũ là sơ đồ runtime v3.

Nguồn sơ đồ kỹ thuật dùng SVG, Draw.io và Mermaid. Draw.io có các khối/connector/icon chỉnh sửa được; không flatten toàn bộ thành ảnh. Icon Lucide được lưu cục bộ kèm giấy phép để hình vẫn mở được khi offline. [Nguồn icon Lucide](https://lucide.dev/), [Draw.io](https://www.drawio.com/), [Mermaid](https://mermaid.js.org/).

Các lựa chọn này được chọn theo tính chỉnh sửa và khả năng thể hiện quan hệ, không có dữ liệu để xếp hạng “plugin phổ biến nhất”. Không cần cài toàn bộ Figma, Miro, Whimsical hoặc tldraw cùng lúc; chọn một workspace nếu cần cộng tác trực tiếp.

## 2. Danh mục sơ đồ và câu hỏi

| File | Mức | Câu hỏi / cách đọc |
|---|---|---|
| 01_tong_quan_he_thong.svg | Tổng quan năng lực | Ai sử dụng, nhóm module gì, nền tảng gì? |
| 02_chuoi_gia_tri.svg | Quy trình và bàn giao | Từ quyền lợi tới cải tiến có ai quyết định và đầu ra nào? |
| 03_quan_he_module.svg | Kiến trúc logic | Module cung cấp dữ liệu gì và nhận gì? |
| thiet_ke_doanh_nghiep.drawio | Bốn trang chỉnh sửa | Business overview/value/module relations và Agent Harness |
| index.html | Sổ sơ đồ cục bộ | Chuyển tab, phóng to và tải nguồn không cần mạng |
| 05_agent_harness.svg | Runtime AI | Single orchestrator, gateway, durable state và observability |
| ai_*.svg / ai_*.mmd | AI phân rã | State/sequence/RAG/loop/HITL/evaluation/scenario từ 9 tài liệu |
| Mermaid trong 10 bản module | Phân rã | Decision, trạng thái, error path và bàn giao riêng |
| Mermaid ER trong 02 | Conceptual data | Phân biệt request/incident/work order/visit và ledger |

Các mức là quy ước tài liệu; không gọi tổng quan capability là diagram deployment hoặc DFD. Actor, business module và nền tảng có kiểu khác nhau; arrow có tên; icon chỉ giúp nhận diện, không thay tên và trách nhiệm.

## 3. Quy ước hình

- Màu xanh dương: cam kết và tiếp nhận; xanh lá: thực thi và thiết bị; amber: vật tư/cung ứng; cyan: tài chính/báo cáo.
- M09 là Knowledge Domain. Agent Harness là runtime ngang M01-M10; hình 05 phân rã context/planner/controller/observation/evidence/policy, state và gateway. M10 giữ authority nghiệp vụ.
- Đường nối có hướng chỉ thông tin/sự kiện trao đổi; không suy ra REST call hoặc microservice nếu chưa có thiết kế thực thi.
- Hình overview dùng nền tảng ERPNext như ứng viên hiện thực bên dưới; module tồn tại về nghiệp vụ trước lựa chọn nền tảng.
- Hình hành trình là nghiệp vụ, không cần mọi bước xảy ra tuyến tính: chờ/đổi scope/đi lại có vòng riêng trong module.

## 4. Cách trình bày với giảng viên

Mở tổng quan, nêu giá trị AIS bán và ca máy hỏng có nhiều người quyết định. Chọn pain point hợp đồng, điều phối sai nguồn lực và vật tư bị hứa trùng; đi qua user story và chỉ module trên hình. Dùng chuỗi giá trị để chỉ đầu ra/điểm bàn giao. Khi được hỏi sâu, mở file module đúng mã để xem workflow, state, data và AC; dùng ER khi cần phân biệt đối tượng.

Không mở slide đầu bằng toàn bộ trường custom/DocType. Không trình bày số demo như baseline; không gọi các giả thuyết đã khảo sát. Tách “mục tiêu thiết kế”, “lát cắt MVP” và “có mã hiện tại” theo bản đối chiếu.

## 5. PDF tham khảo

[KTHT_MSTeams.pdf](D:/Downloads/KTHT_MSTeams.pdf) có 6 trang, trang 6 trống. Trang 1/2 chia clients-services-platform, trang 3 kiến trúc logic, trang 4 RAG ingestion/query, trang 5 orchestration và nguồn dữ liệu. Đã đọc trực quan vì PDF không có lớp text.

Vận dụng cách phân tầng và tách detail RAG; không sao chép Graph API, Azure, Teams calling hoặc cloud storage vào sơ đồ AIS. Hình tham khảo không chỉ định thầy đã yêu cầu công nghệ hoặc số lượng module nào.

## 6. Duy trì nguồn và kiểm tra

`diagrams/build_diagrams.py` sinh SVG và Draw.io từ cùng cấu trúc; source icon nằm ở `diagrams/icons/`. PNG được render qua trình duyệt Edge/Playwright; không dùng engine SVG làm mất nét đứt/arrowhead. `diagrams/index.html` không tải script từ CDN.

`diagrams/render_diagrams.py` dùng Mermaid library từ CLI bundle 11.12.0 đã cache, render qua `render_mermaid.cjs` với Playwright/Edge. Loopback server tạm chỉ phục vụ thư mục library và đóng sau render; không dùng browser Puppeteer cũ đang lỗi trên máy này. Có thể render chọn hình bằng `python docs/design/diagrams/render_diagrams.py --only 04_mo_hinh_du_lieu,ai_* --skip-previews`. [Trang xem 10 luồng](diagrams/module_review.html) giúp kiểm tra tổng hợp; sổ sơ đồ có cả các luồng AI.

Khi sửa PP/US hoặc ranh giới module, sửa file module/kiến trúc và source diagram, regenerate rồi kiểm tra: chữ không tràn, arrow không đi qua chữ, legend rõ, tên/mã đúng, links không thiếu. Sửa thủ công Draw.io không tự đồng bộ ngược về generator, nên cần chọn một nguồn chính và cập nhật còn lại.

Tệp `design_manifest.json` ghi file, số từ, mã truy vết và kiểm tra links. Đây là kiểm tra cấu trúc tài liệu, không chứng minh yêu cầu doanh nghiệp được xác nhận hoặc runtime đã đáp ứng.
