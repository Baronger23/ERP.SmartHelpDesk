# Bộ thiết kế doanh nghiệp Smart HelpDesk & Maintenance

Phiên bản 3.0 · 08/10/2026 · Doanh nghiệp dịch vụ bảo trì công nghiệp B2B.

Bộ này đi từ doanh nghiệp đến giải pháp. AIS là bối cảnh giả định đã được người dùng chọn; mã nguồn hiện tại chỉ dùng ở bước đánh giá khoảng cách. Không coi danh mục có sẵn, mã demo hoặc giới hạn của một DocType là giới hạn nhu cầu của doanh nghiệp.

## Trình tự đọc

| Mức | Tài liệu | Câu hỏi cần trả lời |
|---|---|---|
| 0 | [Tổng quan hệ thống](00_tong_quan_he_thong.md) | AIS tạo giá trị gì, ai tham gia và cần những năng lực nào? |
| 1 | [Phân tích doanh nghiệp và yêu cầu](01_phan_tich_doanh_nghiep_va_yeu_cau.md) | Pain point suy ra từ đâu; story và tính năng giải quyết chúng như thế nào? |
| 1 | [Kiến trúc logic và dữ liệu](02_kien_truc_logic_va_du_lieu.md) | Các module trao đổi gì, ai sở hữu dữ liệu và đâu là ranh giới? |
| 2 | [Mười bản phân rã module](#cac-ban-phan-ra-module) | Quy trình, quy tắc, trạng thái, ngoại lệ và nghiệm thu cụ thể ra sao? |
| 3 | [Lộ trình và đối chiếu](03_lo_trinh_va_doi_chieu.md) | Có thể triển khai trên ERPNext như thế nào, phần nào còn thiếu? |
| Xuyên suốt | [Hướng dẫn sơ đồ](04_huong_dan_so_do.md) | Cách mở, sửa, đọc các loại sơ đồ và công cụ sử dụng |
| Chuẩn domain | [Hợp đồng workflow](05_domain_workflow_contracts.md) | WorkSource, ownership sự kiện, P1 atomic reservation/approval, KPI late events |
| AI runtime | [9 bản thiết kế Agent Harness](ai_architecture/readme.md) | Planning, durable orchestration, RAG, tools, HITL, security, evaluation và E2E |

<a id="cac-ban-phan-ra-module"></a>

## Các bản phân rã module

| Mã | Module | Kết quả doanh nghiệp cần |
|---|---|---|
| M01 | [Khách hàng và hợp đồng](modules/m01_khach_hang_va_hop_dong.md) | Biết đang phục vụ ai, ở đâu, theo quyền lợi và cam kết nào |
| M02 | [Tiếp nhận và SLA](modules/m02_tiep_nhan_va_sla.md) | Mọi yêu cầu có người chịu trách nhiệm và thời hạn rõ ràng |
| M03 | [Điều phối và tác nghiệp](modules/m03_dieu_phoi_va_tac_nghiep.md) | Đúng người, đúng lần đến hiện trường, có nghiệm thu |
| M04 | [Thiết bị và bảo trì](modules/m04_thiet_bi_va_bao_tri.md) | Hồ sơ kỹ thuật liên tục và kế hoạch phòng ngừa thực hiện được |
| M05 | [Kho và vật tư](modules/m05_kho_va_vat_tu.md) | Có vật tư thật, được giữ chỗ và tiêu hao đúng ca |
| M06 | [Mua hàng và bổ sung](modules/m06_mua_hang_va_bo_sung.md) | Thiếu hàng được mua đúng nhu cầu, nhận đúng chất lượng |
| M07 | [Chi phí và hóa đơn](modules/m07_chi_phi_va_hoa_don.md) | Thu đúng phần khách chấp thuận và hiểu giá vốn dịch vụ |
| M08 | [Báo cáo và KPI](modules/m08_bao_cao_va_kpi.md) | Chỉ tiêu có căn cứ, thúc đẩy hành động thay vì làm đẹp báo cáo |
| M09 | [Tri thức kỹ thuật](modules/m09_tri_thuc_va_tro_ly_ai.md) | Lifecycle/index/retrieval/freshness; không sở hữu runtime agent |
| M10 | [Quản trị và kiểm soát](modules/m10_quan_tri_va_kiem_soat.md) | Phạm vi quyền, phê duyệt và dấu vết được kiểm soát xuyên suốt |

## Sơ đồ và tính chỉnh sửa

- [Sơ đồ tổng quan](diagrams/01_tong_quan_he_thong.svg): lớp người dùng, nhóm năng lực, module và nền tảng.
- [Chuỗi giá trị và bàn giao](diagrams/02_chuoi_gia_tri.svg): từ yêu cầu đến kết quả được chấp nhận và quyết toán.
- [Quan hệ module](diagrams/03_quan_he_module.svg): đường nối có tên thông tin trao đổi.
- [Agent Harness có icon](diagrams/05_agent_harness.svg): runtime ngang, capabilities/gateway và checkpoint.
- [Bản Draw.io nhiều trang](diagrams/thiet_ke_doanh_nghiep.drawio): các khối, icon và connector có thể sửa.
- [Sổ sơ đồ](diagrams/index.html): xem và chuyển giữa các sơ đồ ngay trong trình duyệt.
- [Bản Canva v2 đã duyệt](https://canva.link/bucs6cajm4rbjqc): capability map trước nâng cấp Harness; bản runtime v3 ở SVG/Draw.io/Markdown cục bộ.

Tài liệu có 20 giả thuyết pain point, 48 user story, 60 chức năng domain và 8 năng lực runtime AH-F01–08. `PP-xx`, `US-xx`, `Mxx-Fxx`, `AC-xx` là vấn đề, nhu cầu, chức năng và tiêu chí; HT/DC là test oracles. Tên file/tiêu đề dùng chữ thường/sentence case, giữ chữ viết tắt.

## Cách quản lý thay đổi

Phiên bản 2 thay đổi phân rã module: thêm hợp đồng và quản trị thành module có thiết kế riêng; kiến thức đã duyệt là năng lực nghiệp vụ, AI là mở rộng của nó. Mã M của phiên bản trước không giữ nguyên ý nghĩa. Khi trích dẫn, dùng tên module và phiên bản 2 cùng mã.

Phiên bản 3 giữ 10 module và chuẩn hóa WorkSource/ownership/P1/KPI; tách Harness khỏi M09, bổ sung 9 tài liệu AI cùng schemas/fixtures/checker. US-35/36 chuyển ownership runtime; M09-F04–06 là ingestion/hybrid retrieval/freshness. Tên file M09 giữ để links cũ không gãy. [Bản đối chiếu](03_lo_trinh_va_doi_chieu.md) ghi rõ design contracts/offline conformance khác runtime đã triển khai.

Mỗi pain point ở đây là **suy luận thiết kế cần kiểm chứng**, không phải phỏng vấn đã diễn ra. Chưa công bố số nhân viên, lượng ca, chi phí hoặc tỷ lệ cải thiện thực tế khi không có bằng chứng.
