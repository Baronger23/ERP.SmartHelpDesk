"""Build a self-contained GPT web diagram brief from canonical design sources.

Run after build_diagrams.py and render_diagrams.py. Copies all graph definitions
and native diagram labels, then adds manual layout briefs and semantic checks.
"""
from pathlib import Path
import importlib.util
import hashlib
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location('ais_diagrams', HERE / 'build_diagrams.py')
diagrams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagrams)

# name, title, source, layout, intent, semantic constraints
SPECS = [
('01_tong_quan_he_thong', 'Tổng quan năng lực doanh nghiệp', '00_tong_quan_he_thong.md', 'Poster ngang 16:10; actor ở trên, kênh bên dưới, lưới 3×3 M01–M09, hai dải ngang Harness/M10 và nền tảng ở đáy.', 'Cho người xem thấy AIS cung cấp dịch vụ bảo trì B2B, ai sử dụng và hệ thống được chia thành những trách nhiệm nào.', 'Đủ M01–M10 đúng tên. Harness là runtime ngang, không là M11. M10 giữ quyền/policy/approval. Hotline/Zalo là nhập hộ ở phạm vi ban đầu. ERPNext/Frappe là ứng viên hiện thực; không vẽ thành nhiều microservices. Nhóm người dùng không hàm ý mọi người thấy mọi dữ liệu.'),
('02_chuoi_gia_tri', 'Chuỗi giá trị và điểm bàn giao', '00_tong_quan_he_thong.md', 'Ngang 16:9; sáu thẻ bước đều nhau; ba thẻ ngoại lệ dưới chuỗi; dải kiểm soát ở đáy.', 'Giải thích dịch vụ tạo giá trị qua cam kết, tiếp nhận, chuẩn bị, thực hiện, quyết toán và cải tiến.', 'M03 ghi khôi phục và nghiệm thu; M07 nhận bằng chứng để đối soát phí. Phát sinh cần duyệt trước khi làm phần vượt phạm vi. Giữ chỗ atomic ở M05. PM xong không tự đóng finding. Chuỗi chính không có nghĩa mọi ca chỉ đi một lần hoặc luôn tuần tự. Khôi phục ≠ nghiệm thu ≠ hóa đơn ≠ thanh toán.'),
('03_quan_he_module', 'Quan hệ và hợp đồng bàn giao module', '02_kien_truc_logic_va_du_lieu.md', 'Poster 4:5 hoặc 16:15 rộng; lưới module theo nguồn nguồn lực/tài chính; connector vuông góc; bảng bàn giao bổ sung dưới hình; M10/Harness ngang ở đáy.', 'Thể hiện nguồn và đích của dữ liệu/sự kiện, thay vì chỉ đặt các module cạnh nhau.', 'Giữ tất cả mũi tên và các dòng bàn giao bổ sung. M03→M02 là facts, M02 chỉ phản chiếu. M04→M03 có kỳ PM/checklist. M01→M07 có quyền lợi theo snapshot. M03/M04→M09 là lesson sau review. M09→Harness/M03 là evidence. M01–M07→M08 theo kỳ/quyền. Harness đi qua gateway, không ghi trực tiếp database. Các đường là quan hệ logic, không xác định giao thức mạng.'),
('04_mo_hinh_du_lieu', 'Mô hình dữ liệu nghiệp vụ khái niệm', '02_kien_truc_logic_va_du_lieu.md', 'Poster ngang 3:2; bốn vùng: khách/cam kết, nguồn công việc, PM/tác nghiệp, nguồn phí/hóa đơn. Crow’s foot rõ, thêm hộp constraints.', 'Phân biệt các đối tượng thường bị gộp vào một Issue và giữ đúng quan hệ một/nhiều/optional.', 'WorkSource XOR: đúng một FK Incident, ServiceRequest không có Incident hoặc PMOccurrence. UNIQUE nguồn và UNIQUE(source_id,package_key,generation_version). Kỳ PM UNIQUE(plan_version_id,equipment_id,period_key). Không đọc ba đường optional thành cho phép ba nguồn cùng lúc. ChargeLine có đúng một loại nguồn phí; Consumption/TimeLog optional theo loại, không bắt mọi dòng phí có cả hai. Đây là lát cắt conceptual, không phải schema/DDL đầy đủ.'),
('05_agent_harness', 'Tổng quan Agent Harness có icon', 'ai_architecture/01_agent_harness_architecture.md', 'Poster ngang 4:3; gateway trên, khung single orchestrator ở giữa, sáu thẻ capabilities trong khung, loop riêng, ba cột M09/gateway/state bên dưới, domain và observability ở đáy.', 'Giải thích cách bộ điều hành giúp AI thực hiện nhiệm vụ nhiều bước trong quyền và có tiến độ bền vững.', 'Có context/intent, planner, controller, observation/evaluator, evidence verifier, policy gate; state/checkpoint và final result. Đọc/proposal/draft được duyệt thuộc baseline, không giữ hàng thực/submit/override/close. M09 không sở hữu run; M10/ERP là authority approval. Checkpoint không thay transaction ERP. Offline contract PASS không là ERP/LLM integration PASS.'),
('m01_luong_nghiep_vu', 'M01 — Khách hàng và hợp đồng', 'modules/m01_khach_hang_va_hop_dong.md', 'Ngang 16:9; sáu bước chính; nhánh phụ lục/gia hạn đi xuống rồi hiển thị version mới, không ghi đè version cũ.', 'Đi từ thông tin khách/site/người liên hệ đến điều khoản hiệu lực và snapshot dùng cho từng ca.', 'Người liên hệ khác người có quyền duyệt. Coverage áp theo thiết bị/site/ngày hiệu lực. Snapshot của ca giữ version; thay hợp đồng không hồi tố. Nhánh version mới không tự sửa snapshot cũ. Chưa đủ authority/coverage thì cần xác minh, không tự coi toàn bộ Customer là VIP.'),
('m02_luong_nghiep_vu', 'M02 — Tiếp nhận và SLA', 'modules/m02_tiep_nhan_va_sla.md', 'Dọc 4:5; hình thoi trùng ca, hai nhánh nhập lại ở timeline; hình thoi điều kiện đóng ở cuối.', 'Nhận báo lỗi, tránh trùng, xác định cam kết và theo dõi đến khi có đủ facts để đóng yêu cầu.', 'Mốc thực khác creation. Liên hệ trùng nối ca chủ và tiếp tục nhận cập nhật. WorkSource không nhân đôi theo tin báo cùng incident. Khôi phục/nghiệm thu do M03 ghi; M02 nhận facts, không tự tạo bằng chứng. Chờ không tự động pause SLA; policy/lịch phải xác định. Chưa đủ điều kiện đóng quay lại theo dõi.'),
('m03_luong_nghiep_vu', 'M03 — Điều phối và tác nghiệp', 'modules/m03_dieu_phoi_va_tac_nghiep.md', 'Dọc 4:5 hoặc ngang 3:2 hai lane; lane tác nghiệp chính và lane facts chuyển M02/M07; nhánh chờ/visit tiếp theo và pending acceptance dễ thấy.', 'Một lệnh việc có nhiều lần thực hiện, có kết quả khôi phục và người đúng quyền nghiệm thu.', 'Visit không ghi đè lượt trước. Scope/fee đổi phải duyệt version mới. Chưa đủ nguồn lực chưa đi tiếp. Accepted là điều kiện hoàn theo flow; pending/rejected giữ lý do và action. Khôi phục có tiêu chí thử máy. M03 phát facts, không tự đóng request hay sửa SLA. Quality review sâu có thể mở rộng sau nhưng không bỏ nghiệm thu cơ bản.'),
('m04_luong_nghiep_vu', 'M04 — Thiết bị, kỳ PM và findings', 'modules/m04_thiet_bi_va_bao_tri.md', 'Dọc 4:5; một chuỗi plan→occurrence→checklist, nhánh không lỗi/có lỗi và mỗi finding phân loại; hộp finding còn mở dưới kết thúc PM.', 'Tách kế hoạch tổng, từng kỳ đến hạn, kết quả kiểm tra và các việc phát sinh.', 'Nguồn work order là PMOccurrence, không phải toàn bộ plan. Checklist/version và ngày hạn gốc được giữ. Một kỳ có nhiều finding. PM hoàn thành sau đủ checklist/phân loại nhưng không tự đóng findings. Tạo/liên kết Incident từ finding chống trùng khi retry. Equipment khách không tự trở thành vốn của AIS; số đo có thể nhập tay, không tự thêm IoT.'),
('m05_luong_nghiep_vu', 'M05 — Giữ chỗ, cấp, dùng và trả vật tư', 'modules/m05_kho_va_vat_tu.md', 'Dọc 4:5 hoặc ngang 3:2; transaction hold là khối nổi bật; nhánh thiếu/xung đột quay lại kiểm tra; cấp/dùng/trả chia lane.', 'Ngăn hai ca cùng hứa một vật tư và theo dõi đúng vật tư thực dùng.', 'Đọc thấy đủ chưa là hold thành công. Transaction recheck+lock/CAS+idempotency. Hai hold không vượt available. Transfer/cấp khác tiêu hao; dùng rồi đối soát phần hold, trả/thu hồi có nguồn. Direct issue từ kho tổng có thể dùng, không bắt mọi ca đi qua xe. Timeout đọc kho là chưa biết, không là shortage; hold runtime phải do workflow nghiệp vụ.'),
('m06_luong_nghiep_vu', 'M06 — Nhu cầu ròng và mua bổ sung', 'modules/m06_mua_hang_va_bo_sung.md', 'Dọc 4:5; decision cần mua ở trên, branch không tạo MR kết thúc riêng; nhận hàng accepted/rejected song song; phần còn thiếu ở đáy.', 'Mua phần thực sự thiếu, nhận từng phần và cập nhật ca chờ.', 'Tính available và nguồn cung mở để tránh mua lặp. MR/PO có nguồn và chống trùng. Accepted làm tăng lượng dùng được; quarantine/reject không tăng khả dụng dù có thể có sổ kho riêng. Nhận một phần giữ phần chưa đáp ứng, ETA và nguồn thay thế có thẩm quyền. Không tự coi PO đã đặt là hàng đã có.'),
('m07_luong_nghiep_vu', 'M07 — Duyệt phát sinh và quyết toán', 'modules/m07_chi_phi_va_hoa_don.md', 'Dọc 4:5; coverage/estimate/approval ở trên, gate hiện tại trước M03 thực hiện, đối soát và pending/invoice ở dưới.', 'Khách chấp thuận đúng phạm vi trước thực hiện và hóa đơn truy về nguồn công/vật tư.', 'Approval đúng actor/scope/hash/version/expiry. Thay nội dung phải duyệt lại. M03 sở hữu acceptance, M07 sử dụng fact. Phân biệt AIS chịu/bảo hành/khách trả. Charge có nguồn không thu lặp. Nháp→duyệt→submit là workflow con người có quyền, không là permission để agent submit hóa đơn. Nghiệm thu không đồng nghĩa đã thanh toán.'),
('m08_luong_nghiep_vu', 'M08 — KPI có nguồn và phiên bản', 'modules/m08_bao_cao_va_kpi.md', 'Ngang 16:9; pipeline dữ liệu có lane sự kiện đến muộn/correction quay lại nguồn; snapshot cũ/mới minh họa ở đáy.', 'Tính báo cáo từ dữ liệu đủ, có thể drill-down và giữ lịch sử khi số liệu thay đổi.', 'Có scope/kỳ/as_of/watermark/formula/policy version. Dedup event và supersedes correction tránh cộng đôi. Dữ liệu thiếu/chưa đủ cửa sổ FTFR không bị coi đạt. Late callback có thể sửa kỳ ca gốc bằng revision mới, giữ bản công bố cũ. Không thêm tỷ lệ 100% hoặc số cải thiện chưa đo.'),
('m09_luong_nghiep_vu', 'M09 — Vòng đời tri thức và retrieval', 'modules/m09_tri_thuc_va_tro_ly_ai.md', 'Ngang 3:2 với hai lane: ingestion/publish và query/retrieval; live catalog nối cả hai.', 'Nguồn tri thức được quản lý trước khi trở thành bằng chứng cho người dùng hoặc Harness.', 'Parse giữ page/bảng/đơn vị. Metadata thiếu đi quarantine. Staging không là published. Trusted scope/model/status/effective trước retrieval, recheck nguồn hiện tại sau rerank. Evidence có page/version/conflict. M09 không lập kế hoạch nhiệm vụ và không ghi chứng từ ERP.'),
('m10_luong_nghiep_vu', 'M10 — Quyền, approval và audit', 'modules/m10_quan_tri_va_kiem_soat.md', 'Dọc 4:5; permission gate và approval gate riêng; đỏ cho từ chối, xanh cho thành công, audit ở cuối.', 'Mọi kênh thao tác phải đi qua quyền và kiểm soát nghiệp vụ tại máy chủ.', 'Không được phép đi thẳng tới reject và audit phù hợp quyền. Có quyền đọc không có nghĩa có quyền duyệt/ghi. Approval tối thiểu là P1, matrix nhiều cấp là mở rộng. Gate xét field/file/API/export. Valid approval vẫn cần business validation; retry không tạo effect trùng. Ẩn nút UI không thay server permission.'),
('ai_01_agent_harness_architecture_01', 'AI — Kiến trúc thành phần', 'ai_architecture/01_agent_harness_architecture.md', 'Ngang 16:9; gateway ở trái/trên, orchestrator giữa, thành phần controller quanh tâm, hai capability M09/ERP bên phải, state/observability dưới.', 'Bản kỹ thuật của kiến trúc Harness, thể hiện đường đi giữa các thành phần.', 'Một orchestrator có các capabilities, không mặc định nhiều agents. Policy gate kiểm tool trước ERP. Durable state hai chiều với Harness. M09 là capability truy tri thức riêng. Business authority ở M01–M08/M10. Không vẽ LLM kết nối trực tiếp bảng nghiệp vụ.'),
('ai_02_agent_orchestration_workflow_01', 'AI — Vòng đời nhiệm vụ', 'ai_architecture/02_agent_orchestration_workflow.md', 'Ngang 3:2; trạng thái thực thi ở giữa, WAITING ở trên, terminal ở dưới; label transition rõ.', 'Phân biệt chạy, chờ, tiếp tục, xác minh và các loại kết thúc.', 'Giữ tên state machine nguyên văn. WAITING lưu checkpoint/release worker/HTTP/LLM. Resume cần auth event, dedup/CAS/lease/revalidate. COMPLETED chỉ đạt objective, có thể là draft. PARTIAL có facts đã xác nhận; BLOCKED khác FAILED. Terminal không tự mở lại; continuation tạo run mới. CANCELLED không tự rollback effect đã APPLIED.'),
('ai_02_agent_orchestration_workflow_02', 'AI — Sequence thực thi có giới hạn', 'ai_architecture/02_agent_orchestration_workflow.md', 'Ngang 16:9; năm lifeline User/Harness/State store/Tool gateway/ERP-M09; loop nằm trong khung.', 'Thấy thứ tự đọc facts, lưu plan và thực hiện ready steps có checkpoint.', 'Trusted session tại đầu vào. Data có versions/observed_at. Lưu step/counter/checkpoint mỗi bước. Loop bounded, không reset budget khi replan. Reads độc lập có thể parallel theo limit; dependencies model/scope phải giữ thứ tự. Gateway là mặt logic; retrieval M09 không được coi là ghi ERP. Final có verified/partial/waiting.'),
('ai_02_agent_orchestration_workflow_03', 'AI — Sequence prepare, approve và commit', 'ai_architecture/02_agent_orchestration_workflow.md', 'Poster ngang 3:2; năm lifeline, một khung ALT ba nhánh; transaction màu amber và note crash/reconcile.', 'Người duyệt exact binding; gateway không tạo effect trùng khi retry và commit có tính nguyên tử.', 'Notification không là authority: Harness đọc quyết định lại. CAS/lease trước dispatch. Lookup receipt cùng key/hash/scope trước kiểm approval mới: APPLIED trả cũ dù đã consume/expired, nếu còn quyền đọc receipt. Key khác hash conflict; command mới stale bị chặn. Draft+consume approval+receipt+outbox trong cùng ERP transaction. Crash sau commit tra receipt cùng key, không key mới.'),
('ai_03_agent_state_and_memory_01', 'AI — Dữ liệu runtime và authority', 'ai_architecture/03_agent_state_and_memory.md', 'Ngang 3:2; ranh giới runtime store bên trái và ERP authority bên phải; ER cardinality, hộp metadata/lease dưới.', 'Tách plan/checkpoint/evidence runtime khỏi business approval và command receipt.', 'Definition/version pinned; step logical identity ổn định, tool attempts riêng. Checkpoint có state_version/CAS, counters và pending command keys. ApprovalRef chỉ tham chiếu authority, không tự tạo quyết định. Session memory không thay stock/permissions. Không lưu raw chain-of-thought. ER là lát cắt; Lease/fencing có trong tài liệu dù không là node của graph hiện tại.'),
('ai_04_rag_ingestion_and_retrieval_01', 'AI — Nạp và công bố tri thức', 'ai_architecture/04_rag_ingestion_and_retrieval.md', 'Ngang 16:9 hoặc dọc 4:5; bước staging→review→publish rõ, quarantine là nhánh màu amber.', 'Tạo index từ nguồn được phép dùng và công bố đúng phiên bản.', 'Kiểm source/file/hash/scope; OCR giữ trang/bảng/đơn vị. Metadata không đủ không publish. Lexical+vector, retrieval tests trước reviewer publish. Active generation chuyển atomic, cache invalidation theo event. Live catalog vẫn kiểm tra quyền/thu hồi ngay cả index lag. Không thêm bước tự học mọi chat thành SOP.'),
('ai_04_rag_ingestion_and_retrieval_02', 'AI — Tìm kiếm và kiểm chứng nguồn', 'ai_architecture/04_rag_ingestion_and_retrieval.md', 'Ngang 16:9; lexical/vector hai nhánh cân đối, merge→rerank→evidence→verifier.', 'Tìm đúng mã/model và cả ý nghĩa triệu chứng, sau đó kiểm phù hợp trước trả lời.', 'Resolved model/trusted scope trước query. Eligibility trước retrieval và recheck applicability/version/source sau rerank. Evidence có page/version/conflict. Similarity không thay quyền hoặc độ đúng. Thiếu nguồn/mâu thuẫn không bỏ qua; verifier trả partial/hỏi thêm theo policy. Chỉ số confidence không là bằng chứng.'),
('ai_05_tool_registry_and_contracts_01', 'AI — Gate công cụ và giao dịch', 'ai_architecture/05_tool_registry_and_contracts.md', 'Poster ngang 3:2; gate chung trên, ba lane Read/Prepare/Approved draft; nhánh receipt/conflict/stale và unknown ở lane write.', 'Phân biệt đọc, chuẩn bị proposal và ghi draft được duyệt.', 'Schema/allowlist/scope bị từ chối có zero new effects. Same key/same hash trả receipt; same key/different hash conflict. Command mới lock/recheck scope/policy/version/expiry. Commit atomic draft+approval+receipt+outbox. APPLIED trả kết quả; chỉ UNKNOWN cần reconcile trước retry. Không vẽ submit/reserve như effect enabled. Context actor/admin không do model cấp.'),
('ai_06_reasoning_planning_execution_01', 'AI — Vòng lặp lập kế hoạch và đánh giá', 'ai_architecture/06_reasoning_planning_execution.md', 'Ngang 3:2; vòng chính clockwise với label; stop/wait/reconcile đặt ngoài vòng, final bên phải.', 'Kết quả mỗi hành động quyết định bước tiếp theo trong giới hạn.', 'Kiểm lease/permission/limits trước dispatch. Observation typed fact/error/unknown/conflict. Persist evidence/counters/checkpoint. Đủ evidence phải verify claims/final policy. Cần người thì checkpoint wait; write unknown reconcile cùng command. Replan tăng version nhưng không reset budget. Final phải nêu pending effect, không suy success từ HTTP 200.'),
('ai_07_security_and_human_approval_01', 'AI — Human approval và tiếp tục', 'ai_architecture/07_security_and_human_approval.md', 'Ngang 16:9; sáu lifeline, note checkpoint trên, approval authority khác Harness, ALT valid/stale dưới.', 'Chờ người có thẩm quyền và tiếp tục mà không tin một callback tự khai approved.', 'Immutable binding/hash/version/scope/expiry. Approver xác thực ghi quyết định ở M10. Notification chỉ tín hiệu. Read authoritative, inbox dedup/CAS/fenced lease. Lookup prior APPLIED receipt trước new-command checks; receipt cũ không consume lần hai. Command mới expired/revoked/stale có zero new effects. Chữ commit ở đây chỉ draft enabled.'),
('ai_08_observability_and_evaluation_01', 'AI — Các cổng đánh giá và phát hành', 'ai_architecture/08_observability_and_evaluation.md', 'Ngang 16:9; bốn cổng nối tiếp, hình thoi critical gates, nhánh sửa và quay lại có label.', 'Chỉ mở baseline sau kiểm tra contracts, tích hợp, chất lượng nguồn/model và pilot.', 'Offline conformance không thay ERP fault/concurrency/auth tests. Holdout có expert gold. Pilot đo traces/cost/recovery/limits. Critical gate fail chưa release. Rollback bundle gồm phiên bản/policy liên quan. Không vẽ đã đạt production hoặc accuracy 100%; các mốc sau offline chưa được chạy trong phiên kiểm tra này.'),
('ai_09_end_to_end_agent_scenarios_01', 'AI — Kịch bản kỹ thuật và vật tư xuyên suốt', 'ai_architecture/09_end_to_end_agent_scenarios.md', 'Poster ngang 3:2; năm lifeline KTV/Harness/M09/ERP Gateway/Approval authority; ALT stock timeout và verified stock.', 'Kết hợp dữ liệu máy, tài liệu và kho để chuẩn bị đề xuất có căn cứ.', 'AC-102 và vật tư/mã lỗi là ví dụ synthetic, không là hướng dẫn nhà sản xuất. Timeout→PARTIAL, không stock=0/MR tự động. Verified compatibility/available/held/version trước proposal. Đọc authoritative approval sau notification, dedup/CAS/revalidate. APPLIED chỉ draft; UNKNOWN nêu pending và reconcile cùng key. Không kết luận đã giữ hàng/submit.'),
]

HEADER = '''# Bộ brief và prompt vẽ toàn bộ sơ đồ trên GPT web

Ngày rà soát: 11/10/2026. Phạm vi: **27 sơ đồ nội dung** trong `docs/design/diagrams`: 5 sơ đồ tổng quan/dữ liệu/Harness, 10 workflow module và 12 sơ đồ AI chi tiết. PNG là bản xem của SVG; hai file Draw.io chứa các trang trùng nội dung, không phải hai kiến trúc khác. `index.html`, contact sheet và icon là công cụ xem/tài nguyên, không tính thành diagram nghiệp vụ mới.

File này tự chứa bối cảnh, các quy tắc chuẩn, brief từng hình, nhãn và nguồn graph. GPT web không cần truy cập các đường dẫn local để hiểu nội dung. Link local chỉ phục vụ bạn đối chiếu. Mỗi mục là một ảnh riêng; không ghép cả 27 hình thành một ảnh chứa chữ quá nhỏ.

## 1. Kết quả kiểm tra và sửa sơ đồ

Đã đối chiếu nguồn sơ đồ với tổng quan, kiến trúc logic, hợp đồng domain/workflow, mười bản module và chín bản AI. Mermaid trong tài liệu là nguồn chuẩn cho 23 hình kỹ thuật; generator là nguồn của bốn hình trình bày. Đã render lại để kiểm tra cú pháp và kiểm tra các bản trình bày bằng trình duyệt. Kết quả này xác nhận mức tài liệu/biểu diễn; không nghiệm thu nghiệp vụ chạy trên ERPNext hoặc LLM.

| Vấn đề trước rà soát | Điều đã chỉnh |
|---|---|
| Chuỗi giá trị đặt chữ nghiệm thu trong bước M07, dễ hiểu sai owner | M03 ghi nghiệm thu; M07 nhận fact để đối soát |
| Hình quan hệ module là một tập đường chính, thiếu một số handoff | Thêm bảng handoff chính thức và dải Harness; giữ đủ các quan hệ chuẩn |
| ER khiến mỗi ChargeLine bắt buộc liên kết đồng thời Consumption và TimeLog | Hai liên kết optional theo loại nguồn; thêm ràng buộc đúng một loại nguồn phí |
| M02 nối liên hệ trùng rồi không thể hiện theo dõi tiếp; owner facts chưa rõ | Nối lại timeline, nhận khôi phục/nghiệm thu từ M03, xét điều kiện đóng |
| M03 ghi khách chưa chấp nhận rồi vẫn đi thẳng tới hoàn thành | Tách accepted với pending/rejected và nhánh theo dõi/xử lý lại |
| M04 chưa nêu rõ trạng thái finding độc lập kỳ PM | Thêm note giữ findings mở sau hoàn PM và nguồn work PMOccurrence |
| M05 đọc đủ rồi coi giữ chỗ luôn thành công | Thêm transaction recheck/lock/CAS/key và decision hold thành công/xung đột |
| M06 chưa có nhánh nhu cầu ròng bằng 0 | Thêm không tạo MR, chống trùng, nhận thiếu/reject và phần còn mở |
| M07 thiếu gate hiệu lực approval trước thực hiện | Thêm scope/hash/version/expiry, receipt facts nghiệm thu từ M03 |
| M08 chưa thể hiện event muộn/correction | Thêm dedup/as_of/watermark/revision và giữ bản báo cáo cũ |
| M10 không vẽ nhánh permission bị từ chối | Thêm explicit permission gate và approval binding tối thiểu |
| Tool graph chưa tách key conflict, stale và unknown | Thêm zero-effect rejection; APPLIED trả receipt, UNKNOWN mới reconcile |
| E2E AI dễ coi decision event là đủ authority | Thêm đọc quyết định nguồn, dedup/CAS/revalidate |
| Lifecycle thiếu hủy trước dispatch/đang resume/verify | Thêm transition CANCELLED cho các state đó; không tự rollback effect |
| Văn bản phân kỳ M03 còn đặt reservation ở P2 | Sửa theo chuẩn M05: atomic reservation tối thiểu P1; M10 cũng nêu approval gate P1 |

Một số workflow chỉ là lát cắt chính, không liệt kê mọi ngoại lệ hoặc FK. Phần “Quy tắc bắt buộc” dưới mỗi hình bổ sung điều không thể diễn đạt hết trong graph. Không vì một đường không xuất hiện ở hình rút gọn mà bỏ quy tắc trong thiết kế.

## 2. Bối cảnh và từ điển để GPT web hiểu đúng

AIS là doanh nghiệp giả định cung cấp dịch vụ bảo trì công nghiệp B2B cho nhiều nhà máy. Doanh nghiệp cần nhận yêu cầu, thực hiện đúng cam kết, phòng ngừa hỏng, chuẩn bị vật tư, kiểm soát chi phí và cải tiến chất lượng. Các pain point là giả thuyết cần khảo sát, không ghi lên ảnh rằng đã được xác nhận hoặc đã cải thiện hiệu suất.

| Mã | Nhãn chuẩn | Trách nhiệm |
|---|---|---|
| M01 | Khách hàng và hợp đồng | Customer/site/authority/coverage/version/snapshot |
| M02 | Tiếp nhận và SLA | Request/triage/clock/timeline/projection/closure |
| M03 | Điều phối và tác nghiệp | WorkOrder/Visit/time log/restoration/acceptance/callback |
| M04 | Thiết bị và bảo trì | Equipment/plan version/PMOccurrence/checklist/Finding |
| M05 | Kho và vật tư | Actual/held/available/reservation/custody/consumption/return |
| M06 | Mua hàng và bổ sung | Net demand/MR/PO/ETA/accepted receipt/shortfall |
| M07 | Chi phí và hóa đơn | Estimate approval/charges/allocation/invoice/reconciliation |
| M08 | Báo cáo và KPI | Source/formula/as_of/watermark/revision/drill-down |
| M09 | Tri thức kỹ thuật | Document lifecycle/ingestion/hybrid retrieval/evidence/freshness |
| M10 | Quản trị và kiểm soát | Identity/scope/policy/authority/audit/restore |

Request là yêu cầu/liên hệ của khách; Incident là sự cố cần khôi phục; WorkOrder là gói việc được giao; Visit là từng lần thực hiện. PMPlanVersion là kế hoạch có phiên bản; PMOccurrence là kỳ cụ thể; Finding là phát hiện có người theo dõi. Snapshot lưu chính sách áp dụng tại thời điểm giao dịch. Reservation giữ hàng, Consumption ghi hàng thực dùng; chuyển kho không là tiêu hao.

Harness là runtime điều hành AI ngang các module, không là module M11. M09 cung cấp tri thức, không sở hữu run/plan. M10/ERP giữ authority phê duyệt. ERPNext/Frappe là ứng viên hiện thực, không phải lý do giới hạn bài toán doanh nghiệp trong một Issue.

## 3. Quy tắc nội dung áp dụng cho mọi ảnh

1. Giữ tên module, mã, chiều mũi tên, nhánh decision và số lượng/optional của ER theo nguồn. Có thể dịch nhãn tiếng Anh sang tiếng Việt ngắn gọn nhưng không thay nghĩa. Giữ nguyên tên state và technical ID khi chúng là hợp đồng dữ liệu.
2. Khôi phục kỹ thuật, khách nghiệm thu, đóng yêu cầu, lập hóa đơn và thanh toán là các mốc riêng. M03 ghi facts kỹ thuật/nghiệm thu; M02 phản chiếu/đóng theo policy; M07 giữ facts tài chính.
3. WorkSource chỉ có đúng một nguồn Incident, Request không gắn Incident hoặc PMOccurrence. Một nguồn nhiều gói việc; retry cùng source/package/version không sinh thêm.
4. PM xong không tự đóng mọi finding. Callback cần phân loại, không phải cứ cùng máy là callback.
5. Giữ chỗ an toàn và approval phát sinh tối thiểu thuộc P1. Tồn actual không là available; hold phải kiểm tra lại trong transaction.
6. Phê duyệt gắn đúng nội dung/hash/version/authority/expiry; đổi scope/giá phải xét/duyệt lại. UI không thay server validation.
7. Dữ liệu ERP là nguồn facts, tài liệu được duyệt là nguồn bằng chứng kỹ thuật. LLM không bịa số kho, điều khoản, mã phụ tùng hoặc quy trình nhà sản xuất.
8. AI baseline: scoped reads, proposal và approved business draft. Không vẽ agent tự giữ hàng thực, submit kho/PO/invoice, ép phân công hoặc đóng ca.
9. Notification không là approval authority. Chờ có checkpoint bền vững; resume xác thực/dedup/CAS/lease/revalidate; counters không reset.
10. Same command key+hash trả receipt đã có; khác hash conflict. Unknown write tra kết quả authoritative cùng key trước retry. Draft/consume approval/receipt/outbox cùng ERP transaction. Hủy run không tự undo effect đã ghi.
11. KPI có công thức/nguồn/kỳ; dữ liệu muộn/correction tạo revision có dấu vết. Không vẽ số cải thiện hoặc accuracy 100% chưa đo.
12. Sơ đồ là **thiết kế mục tiêu**. Không trình bày contracts offline đã đạt như production/ERP/LLM integration đã hoàn thành. Không thêm Azure/Teams/IoT/mobile app/microservices/multi-agent chưa được thiết kế.

## 4. Phong cách và prompt dùng chung

Áp dụng thiết kế sáng, trang nhã cho báo cáo kiến trúc doanh nghiệp. Nền #F8FAFC, thẻ #FFFFFF, tiêu đề #0F172A, nét phân chia #E2E8F0. Xanh #1D4ED8 cho cam kết/tiếp nhận; xanh lá #047857 cho tác nghiệp/thiết bị; amber #B45309 cho kho/mua; cyan #0284C7 cho tài chính/báo cáo; slate cho M09; đỏ #DC2626 chỉ cho lỗi/từ chối. Font Inter hoặc tương đương hỗ trợ đầy đủ dấu tiếng Việt; tiêu đề sentence case, không viết hoa toàn bộ. Mã kỹ thuật dùng monospace nếu cần.

Icon outline kiểu Lucide: nhà máy/khách, tài liệu/hợp đồng, clipboard/yêu cầu, cờ lê/tác nghiệp, máy/thiết bị, kiện hàng/kho, xe đẩy/mua, hóa đơn/phí, biểu đồ/KPI, sách/tri thức, khiên/quản trị, database/state. Icon phụ trợ, luôn có nhãn; không thay box bằng ảnh lớn gây nhiễu.

Connector vuông góc, đầu mũi tên rõ, nhãn nằm trên nền trắng có khoảng hở. Process là rectangle, decision là diamond, state machine dùng rounded state, ER dùng entity/cardinality, sequence dùng lifeline/activation/ALT/loop. Không dùng tranh phối cảnh 3D cho sơ đồ cần đọc quan hệ. Khoảng cách đều; ưu tiên cỡ ảnh cao nhất công cụ cho phép. Nếu chữ quá dày, dùng poster lớn hoặc chia thành panel trong **cùng sơ đồ**, giữ đầy đủ node/edge.

### Prompt khởi đầu — dán cùng file này

```text
Bạn là người thiết kế infographic kiến trúc hệ thống doanh nghiệp. Tôi gửi một brief tự chứa 27 sơ đồ của Smart HelpDesk & Maintenance cho AIS, doanh nghiệp bảo trì công nghiệp B2B. Hãy dùng file này làm nguồn nội dung chính thức.

Trước khi vẽ, xác định mã sơ đồ tôi chọn, liệt kê node/edge/branch và các quy tắc bắt buộc của mục đó. Sau đó tạo một ảnh đẹp, dễ đọc, chính xác theo loại diagram và phong cách chung trong brief. Không tự thêm công nghệ, nghiệp vụ, số liệu hoặc nhãn “đã triển khai”. Nhãn tiếng Việt phải có dấu và sentence case; giữ mã module/state/ID kỹ thuật.

Tôn trọng chiều mũi tên, owner, transaction boundary, các nhánh lỗi/chờ/từ chối và cardinality. Icon chỉ minh họa. Nếu sơ đồ dày, dùng poster lớn hoặc panel rõ ràng thay vì xóa node/edge. Đặt footer: “AIS · Thiết kế mục tiêu v3 · Runtime mới cần triển khai và kiểm chứng”. Không nhét toàn bộ 27 diagram vào một ảnh.
```

### Prompt chọn một hình — thay mã bằng mục cần vẽ

```text
Hãy vẽ sơ đồ mã [mã sơ đồ] trong file brief. Dùng đúng “Mục tiêu”, “Bố cục”, “Quy tắc bắt buộc” và nguồn nhãn/graph của mục này. Trước khi tạo ảnh, kiểm tra đủ node, chiều nối và nhánh. Tạo một ảnh duy nhất với icon outline, bố cục thoáng và chữ tiếng Việt dễ đọc. Giữ chú thích về giới hạn/authority ngay trong hình khi chúng quyết định cách hiểu diagram.
```

### Prompt sửa ảnh sau khi xem

```text
Đối chiếu ảnh vừa tạo với graph và quy tắc của sơ đồ đã chọn. Liệt kê nhãn sai, node thiếu, chiều nối sai, nhánh thiếu và phần chữ khó đọc. Sửa đúng các điểm đó, giữ phong cách hiện tại, giãn bố cục khi cần; không đơn giản hóa bằng cách xóa quan hệ nghiệp vụ. Kiểm tra dấu tiếng Việt, owner khôi phục/nghiệm thu, giới hạn hành động AI và transaction boundary.
```

Ảnh raster cần kiểm tra lại chữ và connector sau sinh. Nếu cần bản kỹ thuật chính xác để bảo vệ hoặc chỉnh sửa, ưu tiên nguồn Mermaid/SVG/Draw.io hiện có; ảnh GPT dùng làm bản trình bày sau khi đối chiếu. Không cần cài plugin mới chỉ để dùng brief này.

## 5. Danh mục đầy đủ

'''


def main():
    canvases = {c.name: c for c in [diagrams.overview(), diagrams.journey(), diagrams.relationships(), diagrams.agent_harness()]}
    expected = {p.stem for p in HERE.glob('*.svg')}
    assert expected == {s[0] for s in SPECS}, (expected, len(SPECS))
    records = []
    lines = [HEADER, '| STT | Mã sơ đồ | Tên |\n|---|---|---|\n']
    for i, (name, title, *_rest) in enumerate(SPECS, 1):
        lines.append(f'| {i:02} | `{name}` | {title} |\n')
    lines.append('\n## 6. Brief chi tiết cho từng ảnh\n')
    for i, (name, title, source, layout, intent, constraints) in enumerate(SPECS, 1):
        ET.parse(HERE / (name + '.svg'))
        records.append({'diagram': name, 'source_document': source,
                        'svg_sha256': hashlib.sha256((HERE / (name + '.svg')).read_bytes()).hexdigest(),
                        'svg_xml_valid': True, 'graph_export_matches_source': True if name not in canvases else None,
                        'canonical_labels_from_generator': name in canvases,
                        'review_scope': 'design semantics and document representation, not runtime'})
        lines.append(f'\n### {i:02}. {title}\n\n**Mã:** `{name}`. **Ảnh đối chiếu:** [{name}.svg]({name}.svg). **Tài liệu chuẩn:** [{source}](../{source}).\n\n**Mục tiêu:** {intent}\n\n**Bố cục:** {layout}\n\n**Quy tắc bắt buộc:** {constraints}\n\n')
        if name in canvases:
            canvas = canvases[name]
            lines.append('**Nhãn nguyên bản theo từng khối:** Giữ đầy đủ nội dung sau; có thể xuống dòng/thu gọn câu mà không đổi nghĩa. Tọa độ không phải yêu cầu cho GPT; bố cục ở trên là hướng dẫn.\n\n')
            for item in canvas.items:
                if item['kind'] == 'text':
                    text = ' · '.join(item['lines'])
                    lines.append(f'- `{item["id"]}`: {text}\n')
            edges = [x for x in canvas.items if x['kind'] == 'edge']
            lines.append('\n**Ý nghĩa đường nối:**\n\n')
            if name == '01_tong_quan_he_thong':
                lines.append('- Kênh tiếp nhận dẫn vào lớp nghiệp vụ; M10 và Harness là hai lớp xuyên suốt. Nền tảng hiện thực nằm dưới, không gán mỗi module cho một server riêng. Các đường kênh là minh họa phân lớp, không là một luồng API cụ thể.\n')
            elif name == '02_chuoi_gia_tri':
                lines.append('- Cam kết → tiếp nhận → chuẩn bị → thực hiện → quyết toán → cải tiến. Ba nhánh PM, thiếu nguồn lực và phát sinh/callback bổ sung chuỗi; không xóa lịch sử để quay lại bước trước. Approval phát sinh xảy ra trước phần thực hiện vượt phạm vi, không đợi quyết toán mới duyệt.\n')
            elif name == '03_quan_he_module':
                relations = ['M01 → M02: quyền lợi', 'M02 → M03: giao việc', 'M03 → M02: kết quả/khôi phục/nghiệm thu', 'M04 → M02: máy/finding', 'M03 → M05: nhu cầu/visit', 'M03 → M07: công/nghiệm thu', 'M07 → M03: duyệt scope/phí', 'M05 → M07: tiêu hao', 'M05 → M06: nhu cầu thiếu', 'M06 → M05: hàng nhận đạt', 'M09 → M04: SOP/model', 'M07 → M08: phí/chứng từ']
                lines.extend('- ' + r + '\n' for r in relations)
                lines.append('- Các quan hệ trong bảng “Bàn giao bổ sung” và hai dải M10/Harness cũng là nội dung bắt buộc, được liệt kê nguyên bản ở trên. Có thể dùng hai panel chính/bổ sung để tránh dây chéo.\n')
            else:
                lines.append('- Người dùng → Agent Gateway → Harness. Harness sử dụng M09 retrieval, ERP Tool Gateway và durable state; gateway đi đến domain authority. Trace/audit/budget/evaluation áp dụng toàn luồng. Vòng Plan → Act → Observe → Evaluate → Replan/Finish là vòng điều khiển, không là giao dịch ERP.\n')
        else:
            mmd = (HERE / (name + '.mmd')).read_text(encoding='utf-8').strip()
            document = (ROOT / source).read_text(encoding='utf-8')
            blocks = [b.strip() for b in re.findall(r'```mermaid\s*\n(.*?)```', document, re.S)]
            assert mmd in blocks, (name, 'export differs from canonical Markdown')
            lines.append('**Nguồn graph chính xác:** Các node/edge/transition/cardinality dưới đây là hợp đồng nội dung. GPT dựng lại bằng hình đẹp, không in nguyên mã lên ảnh.\n\n```mermaid\n' + mmd + '\n```\n')
        lines.append('\n**Lệnh sử dụng:** “Vẽ sơ đồ `' + name + '` theo brief này, giữ đủ quan hệ và quy tắc; chọn bố cục đề xuất, chữ có dấu, icon outline và footer thiết kế mục tiêu.”\n')
    lines.append('''
## 7. Checklist kiểm tra ảnh GPT sinh ra

- Đủ các khối và mọi đường/nhánh trong mục đã chọn, kể cả bảng handoff của hình 03.
- Tên/mã, tiếng Việt và thuật ngữ kỹ thuật đúng; chữ không quá nhỏ hoặc bị cắt.
- Connector không chạy qua chữ; đầu mũi tên và label Có/Không hoặc state transition phân biệt được.
- Có legend/cardinality cho ER, lifeline và ALT/loop cho sequence; không đổi chúng thành process tuyến tính.
- M03 sở hữu khôi phục/nghiệm thu; M02 phản chiếu; M07 quyết toán; M09 tri thức khác Harness runtime.
- Không nói draft là giữ hàng/submit; không nói timeout là tồn 0; approval event không thay quyết định nguồn.
- Những ràng buộc XOR/unique/atomic và giới hạn chưa triển khai được giữ trong callout khi cần.
- Không tự sinh tên hãng/model/cách sửa, tỷ lệ cải thiện, cloud stack hoặc cam kết chính xác tuyệt đối.
- Bản ảnh phù hợp nguồn graph và footer trạng thái thiết kế mục tiêu.

## 8. Nguồn chuẩn và cách cập nhật brief

Nguồn ưu tiên theo nội dung: [workflow contracts](../05_domain_workflow_contracts.md) cho bất biến/ownership/P1; [kiến trúc logic](../02_kien_truc_logic_va_du_lieu.md) cho handoff/ER; bản module cho flow; bản AI cho runtime. [Giải thích và so sánh hệ thống cũ](../06_giai_thich_thiet_ke_va_so_sanh_he_thong_cu.md) cung cấp ví dụ dễ hiểu, không thay các hợp đồng kỹ thuật.

Khi sửa tài liệu, sửa Mermaid tại file thiết kế gốc hoặc generator bốn hình trình bày, render lại, rồi chạy `python docs/design/diagrams/build_gptweb_brief.py`. Script kiểm đủ 27 mã và xác nhận graph export khớp Markdown chuẩn. Brief copy nhãn/graph trực tiếp, nên không cần GPT web mở từng link local. Vẫn review phần mô tả và constraints khi chính sách thay đổi.
''')
    target = HERE / 'thiet_ke_diagram_cho_gptweb.md'
    target.write_text(''.join(lines), encoding='utf-8')
    report = {'review_date': '2026-10-11', 'diagram_count': len(records),
              'canonical_mermaid_exports': len(records) - len(canvases),
              'native_generator_views': len(canvases), 'erp_or_llm_tested': False,
              'limitations': ['Conceptual diagrams are selected views, not every FK or exception.',
                              'Generated raster images require label and relation review.'],
              'diagrams': records}
    (HERE / 'diagram_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Built {target.name}: {len(SPECS)} diagrams, {len(target.read_text(encoding="utf-8").splitlines())} lines.')


if __name__ == '__main__':
    main()
