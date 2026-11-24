# Phân công hoàn thiện Smart HelpDesk & Maintenance cho nhóm 3 người

Ngày lập 23/11/2026. Mốc mã nguồn `d175103` trên nhánh `develop`.

Tài liệu đi kèm là [contract tích hợp nhóm 3 người](contract_tich_hop_nhom_3_nguoi.md), đề xuất ngày 24/11/2026. Các task liên module dùng contract đó để thống nhất input/output, quyền, trạng thái, idempotency và ca nghiệm thu trước khi nối hai đầu. API mới được đánh dấu đề xuất để các thành viên làm mock trong lúc bên cung cấp triển khai.

## 1. Mục tiêu và cách dùng bảng phân công

Nhóm gồm đúng **3 người**, tính cả chủ dự án. Tạm gọi người 1 là **Bạn**, hai thành viên còn lại là **Thành viên 2** và **Thành viên 3**. Có thể thay tên trực tiếp trong tài liệu. Codex hỗ trợ Bạn triển khai, rà soát và tích hợp trong phần việc của người 1.

Mục tiêu bản bàn giao đầu tiên là một chương trình dùng được trên Bench cho khách hàng, điều phối, kỹ thuật viên, kho, mua hàng, kế toán và quản lý. Ba luồng sửa chữa, bổ sung vật tư và PM phải chạy được trên giao diện, có chứng từ thật, đúng quyền và có khả năng phục hồi. AI-1 hỗ trợ KTV tra cứu SOP và lịch sử có dẫn nguồn.

Đây là đề xuất phân việc dựa trên mã nguồn và tài liệu hiện có. Các task **Bắt buộc** là phạm vi hoàn thiện được đề xuất cho bản bàn giao đầu tiên. Các task **Nâng cấp** có người phụ trách dự kiến và chỉ đưa vào đợt triển khai khi nhóm chọn phạm vi tương ứng. Đầu việc đòi hỏi quyết định nghiệp vụ phải ghi quyết định trước khi sửa hành vi.

Chưa có dữ liệu về thời gian rảnh hoặc sở trường từng người, nên thứ tự được chia theo mốc bàn giao. Sau mốc đầu tiên, nhóm điều chỉnh tải theo kết quả thực tế.

## 2. Mốc hiện tại và khoảng trống

### Những gì đã có để kế thừa

- App Frappe chuẩn, chạy bằng Bench, 28 DocType SHD và 10 lối vào module.
- Lõi nghiệp vụ xuyên suốt có idempotency, transaction, audit và kiểm phạm vi dữ liệu.
- Runner `scripts/tests/run_bench_checks.py` dựng site thử từ trắng và kiểm tra các nhóm nghiệp vụ.
- Bộ nghiệm thu ba luồng theo tài khoản giữ vai trò chạy qua cùng API lệnh mà Desk sử dụng.
- API đọc ngữ cảnh AI-1, dữ liệu mẫu và hợp đồng JSON đã có trong commit `d175103`.

Mốc kiểm thử đã ghi nhận ngày 18/11/2026 là 8/8 nhóm đạt trên site thử trắng, gồm kiểm tra ERP context AI-1. Ngày lập kế hoạch chỉ rà soát repo và tài liệu. Các task mới vẫn cần kiểm tra lại sau khi triển khai. Nghiệm thu API theo vai trò hiện có là đầu vào cho nghiệm thu trình duyệt.

| Module | Lõi đã có | Khoảng trống cần xử lý trong kế hoạch | Người chịu trách nhiệm chính |
|---|---|---|---|
| M01 Khách hàng, hợp đồng | Site, authority, hợp đồng phiên bản, snapshot quyền lợi | Dữ liệu triển khai, quy trình đổi phiên bản, cảnh báo sắp hết hạn, trải nghiệm khách hàng | Bạn |
| M02 Tiếp nhận, SLA | Request/Incident, triage, lịch SLA, chờ và ETA | Màn hình tiếp nhận, hàng đợi SLA/ETA, thông báo và nghiệm thu trình duyệt | Thành viên 2 |
| M03 Điều phối, tác nghiệp | WorkSource, WO, kiểm lịch/kỹ năng, visit, giờ công, nghiệm thu, callback | Lịch điều phối, thao tác KTV trên điện thoại, xử lý thay đổi lịch trong phạm vi trạng thái hỗ trợ | Thành viên 2 |
| M04 Thiết bị, PM | Equipment, checklist, occurrence, finding, chuyển finding thành ca sửa | Hồ sơ máy/lịch sử, thao tác checklist thuận tiện, scheduler vận hành có bằng chứng | Thành viên 2 |
| M05 Kho, vật tư | Tồn native, reservation đồng thời, bàn giao, tiêu hao, release | Quản lý giữ chỗ hết hạn, trả vật tư chưa dùng, kiểm kê và bảo vệ kho cách ly | Thành viên 3 |
| M06 Mua hàng | Demand, MR, PO duyệt theo hash, nhận một phần/cách ly | ETA cập nhật, giao thiếu/hàng loại, mua bù và kết thúc demand nhất quán | Thành viên 3 |
| M07 Chi phí, hóa đơn | Dự toán/duyệt, charge, lập hóa đơn nháp native, kiểm submit/hủy | Giao diện đối soát, nghiệm thu submit/thu tiền, điều chỉnh và theo dõi công nợ | Thành viên 3 |
| M08 Báo cáo, KPI | Snapshot có nguồn, SLA/FTFR/PM/tài chính, revision | Dashboard, drill-down và dữ liệu nghiệm thu có ca trễ/thiếu/tái phát | Thành viên 2 |
| M09 Tri thức | Catalog/version/reviewer, publish/revoke, keyword search | Corpus SOP có kiểm duyệt, luồng bài học từ ca, tìm kiếm và nối trợ lý | Thành viên 3 |
| M10 Quản trị, kiểm soát | Role/grant, authority, private file, journal/receipt | Ma trận quyền tối thiểu, kiểm native ERP, thu hồi quyền, backup/restore, CI | Bạn |
| AI Agent Harness | Thiết kế v3, schemas/registry offline, ERP context chỉ đọc | Runtime AI-1, UI, kiểm nguồn, giới hạn thực thi và đánh giá model | Bạn |

Mỗi module có một người chịu trách nhiệm đến lúc nghiệm thu. Khi cần sửa một file do người khác phụ trách, mở task phối hợp với người giữ module để thống nhất API và thứ tự ghép.

## 3. Người 1 — Bạn phụ trách nền tảng, khách hàng, quyền và AI-1

Phạm vi chính gồm M01, M10, tích hợp toàn hệ thống và runtime AI-1. Thành viên 3 chuẩn bị M09 để cung cấp corpus cho AI-1.

### A01 — Bộ dữ liệu triển khai và hợp đồng vận hành · Bắt buộc

- Chuẩn hóa bộ dữ liệu demo bàn giao gồm company, hai khách/site, máy, user, kỹ năng, kho, vật tư, bảng giá và supplier. Tách cấu hình triển khai khỏi fixture test.
- Có hướng dẫn nạp dữ liệu lặp lại được, kiểm trùng và danh sách dữ liệu cần người dùng xác nhận.
- Chốt lịch SLA/timezone, callback window, người duyệt/hạn mức, bảng giá VND, quy tắc kho cách ly và ngưỡng cảnh báo.
- Viết hướng dẫn tạo phiên bản hợp đồng mới, gia hạn và thu hồi. Ca đã tiếp nhận giữ entitlement snapshot cũ, ca mới lấy phiên bản có hiệu lực.
- **Đạt khi** người khác nạp dữ liệu trên staging, tiếp nhận được ca A/B và chứng minh đổi hợp đồng không làm đổi cam kết hồi tố.

### A02 — Quyền tối thiểu và vòng đời tài khoản · Bắt buộc

- Lập bảng cho từng vị trí gồm role AIS, role ERPNext native, grant Service/Inventory/Finance/Knowledge và customer/site/warehouse.
- Thu hẹp các grant `All` đang dùng trong dữ liệu nghiệm thu khi xây cấu hình bàn giao.
- Kiểm KTV tiêu hao trên WO có dự toán bằng quyền tối thiểu. Nếu cần điều chỉnh cách kiểm duyệt tài chính trong command, giữ việc xác minh dự toán và che dữ liệu ngoài nhu cầu thao tác.
- Kiểm cả list, form, API, file, export và chứng từ native được nối với SHD. Thêm role native vẫn phải giữ giới hạn khách/kho đã chốt.
- Có quy trình vô hiệu user/token, bàn giao ca đang mở và truy lại actor lịch sử.
- **Đạt khi** khách A/B, KTV được giao/chưa được giao và người bị thu hồi quyền cho kết quả đúng ở các kênh trên, kèm bằng chứng.

### A03 — Portal khách hàng tối thiểu · Bắt buộc

- Làm trang đăng nhập, gửi yêu cầu gắn đúng máy/site, xem trạng thái, hạn và ETA thuộc phạm vi khách.
- Cho người có Contact Authority xem đúng nội dung dự toán, duyệt/từ chối và nghiệm thu kết quả. Mỗi lượt quyết định kiểm lại quyền, hash, phiên bản và hạn hiệu lực phía server.
- Dùng các command hiện có và xác thực phiên Frappe. Hiển thị rõ chờ duyệt, từ chối và lỗi hết hạn.
- Cùng Thành viên 3 thống nhất dữ liệu hiển thị dự toán. Thành viên 2 cung cấp đường mở trạng thái và luồng xử lý tiếp.
- **Đạt khi** khách tự gửi → theo dõi → duyệt chi phí → nghiệm thu trên trình duyệt, và khách B bị chặn cả truy cập trực tiếp URL/API/file của A.
- **Phụ thuộc** A01, A02 và payload dự toán C04.

### A04 — Runtime và giao diện AI-1 cho KTV · Bắt buộc

- Dùng `smart_helpdesk.ai_context.get_context` để lấy hồ sơ máy, lịch sử và SOP bằng danh tính KTV hiện tại.
- Tạo phần gọi model phía server, cấu hình khóa/model, giới hạn đầu vào, thời gian và số lần gọi. Cho phép kiểm thử bằng model giả lập.
- Tạo giao diện mã máy + câu hỏi + kết quả + nguồn. Câu trả lời nêu ghi nhận, giả thuyết có căn cứ, thông tin còn thiếu và tài liệu hỗ trợ.
- Lưu mã lượt hỏi, trạng thái, phiên bản model/prompt, nguồn được dùng và lỗi cần chẩn đoán. Che bí mật và giới hạn người đọc log theo phạm vi.
- Duy trì tập công cụ chỉ đọc của AI-1. Triển khai phần tối thiểu phù hợp thiết kế single orchestrator và ghi rõ mức năng lực đã hiện thực so với AH-F01–AH-F08.
- **Đạt khi** KTV hỏi máy mẫu trên UI và nhận câu trả lời từ model thật có dẫn đúng ID/revision; SOP có version/source_reference. Người ngoài scope bị chặn. Model/ERP lỗi được báo rõ và lượt hỏi dừng trong giới hạn cấu hình.
- **Phụ thuộc** A02 và corpus C06. Bắt đầu bằng JSON mẫu ngay từ mốc đầu.

### A05 — Đánh giá AI-1 và khả năng thu hồi nguồn · Bắt buộc

- Cùng Thành viên 3 xây bộ câu hỏi có nguồn kỳ vọng. Bao gồm đúng model, sai model, thiếu SOP, mâu thuẫn, nguồn bị thu hồi, văn bản bị cắt và prompt injection trong nguồn.
- Kiểm dẫn nguồn có thực sự hỗ trợ nhận định, ID nguồn giả bị từ chối, timeout không biến thành dữ liệu rỗng và nguồn đổi quyền không tiếp tục xuất hiện ở lượt sau.
- Kiểm câu trả lời đúng scope khi chuyển giữa KTV A/B. Cache nếu có phải gắn danh tính/phạm vi và quy tắc thu hồi.
- Đo thời gian và chi phí thực nghiệm để chọn giới hạn cho demo. Nhóm xem lại nhận định kỹ thuật của các ca tổng hợp.
- **Đạt khi** mọi ca vượt quyền/nguồn giả trong bộ nghiệm thu bị chặn; các ca thiếu/mâu thuẫn được ghi rõ và có báo cáo model thật cùng các hạn chế còn mở.
- **Phụ thuộc** A04, C06. Phần này nghiệm thu AI-1 ở phạm vi tra cứu đã chọn.

### A06 — Bench staging, scheduler, CI và phục hồi · Bắt buộc

- Cấu hình web, worker, scheduler, MariaDB và Redis cho môi trường bàn giao, có lệnh khởi động/dừng và kiểm trạng thái.
- Cấp tài khoản dịch vụ riêng cho PM, KPI và notification. Ghi cấu hình `shd_scheduler_user`, `shd_report_user`, lookback và grant cần thiết.
- Đưa runner một lệnh vào CI hoặc môi trường kiểm thử tự động tương đương, lưu kết quả và trả exit khác 0 khi lỗi. Báo cáo ghi phiên bản DB/runtime thực tế.
- Sao lưu DB, private files, cấu hình cần thiết và khóa mã hóa qua kênh được bảo vệ. Khôi phục lên site biệt lập, kiểm liên kết chứng từ, quyền, file và đăng nhập.
- Rà dữ liệu Issue/Asset/demo cũ. Nếu có nhu cầu giữ, lập mapping, chạy thử migration và đối chiếu trước khi đưa vào site bàn giao.
- **Đạt khi** bản clone tươi dựng được, tự chạy regression, PM/KPI chạy bằng đúng service user và có biên bản restore thành công.
- **Phụ thuộc** cấu hình dữ liệu A01, quyền A02 và ca PM B05. Kiểm CI bắt đầu sớm, restore thực hiện khi đã có dữ liệu liên module.

### A07 — Tích hợp và nghiệm thu bản phát hành · Bắt buộc

- Ghép từng lát nhỏ từ hai thành viên, cập nhật hợp đồng API và runner chung.
- Kiểm upgrade từ mốc `d175103`, giữ chứng từ cũ và chạy migration lại được.
- Nghiệm thu ba luồng toàn trình trên trình duyệt, portal khách và AI-1. Ghi các bước native cần submit/thanh toán cụ thể.
- Tổng hợp hướng dẫn theo vai trò, lỗi còn mở, phạm vi hỗ trợ, cấu hình demo và cách quay về phiên bản đã kiểm chứng.
- **Đạt khi** checklist mục 9 hoàn tất, nhóm khác có thể làm lại theo hướng dẫn.

## 4. Người 2 — Thành viên 2 phụ trách vận hành dịch vụ và KPI

Phạm vi chính gồm M02, M03, M04 và M08, từ tiếp nhận tới thực hiện/khôi phục/nghiệm thu và theo dõi chất lượng.

### B01 — Smoke test Desk và sửa lỗi thao tác theo vai trò · Bắt buộc

- Chạy ba kịch bản có sẵn trong `tests/acceptance.py` bằng trình duyệt và tài khoản đúng vai trò.
- Kiểm nút, dialog, kiểu dữ liệu, giá trị mặc định, payload, chuyển trang, tải lại kết quả và thông báo lỗi.
- Ghi ảnh/video, ID chứng từ và bước lỗi. Sửa lỗi UI thuộc phần dịch vụ, chuyển lỗi kho/mua/tài chính cho Thành viên 3.
- **Đạt khi** điều phối/KTV/quản lý thực hiện được các bước của họ bằng Desk, và các ca hết hạn/sai quyền có thông báo dễ hiểu.

### B02 — Tiếp nhận và hàng đợi SLA/ETA · Bắt buộc

- Làm màn hình ca đang mở với Request, Incident, khách/site, máy, ưu tiên, owner, response_due, restoration_due, lý do chờ và ETA hiện hành.
- Có bộ lọc, phân trang và đường mở hồ sơ. Lấy scope từ người đăng nhập phía server.
- Phân biệt quá hạn phản hồi, quá hạn khôi phục, sắp đến hạn và thiếu mốc. Dùng ngưỡng cấu hình từ A01.
- **Đạt khi** có dataset đúng hạn/trễ/đang chờ/thiếu deadline; màn hình hiển thị đúng và chặn truy vấn chéo scope cả khi tự đổi tham số API.
- **Phụ thuộc** A01 để chốt policy và A02 cho persona test.

### B03 — Lịch điều phối và cập nhật lịch · Bắt buộc

- Hiển thị booking theo KTV/ngày, kỹ năng, khả dụng và tình trạng vật tư cho WO.
- Nối thao tác assign hiện có. Kiểm xung đột lịch và vật tư phía server, hiển thị lý do bị từ chối.
- Hỗ trợ đổi người/slot trong trạng thái mà command hiện cho phép. Mọi nhánh mở rộng sang WO đang làm cần task nghiệp vụ riêng.
- **Đạt khi** lịch hiển thị đúng, chặn hai ca trùng slot, chặn KTV thiếu kỹ năng và giải phóng lịch cũ khi đổi booking hợp lệ; có kiểm tra hai lượt gán cạnh tranh.

### B04 — Luồng KTV và bằng chứng hiện trường · Bắt buộc

- Tạo lối thao tác từ WO được giao để bắt đầu/kết thúc visit, ghi công, nhập kết quả và thử máy.
- Cùng Thành viên 3 nối giữ chỗ/tiêu hao và hiển thị vật tư cần dùng. Cho phép visit chưa hoàn thành dẫn tới lần đến tiếp theo theo workflow hiện có.
- Có đính kèm bằng chứng riêng tư, hiển thị trạng thái kỹ thuật hoàn tất và khách nghiệm thu rõ ràng.
- **Đạt khi** dùng được trên trình duyệt điện thoại, hỗ trợ một ca nhiều visit, ca callback, không nhầm khôi phục với nghiệm thu và file ngoài scope bị chặn.
- **Phụ thuộc** C01 cho thao tác vật tư và A02 cho quyền/file.

### B05 — Hồ sơ máy và PM vận hành được · Bắt buộc

- Làm trang máy có model/serial, lịch sử WO/PM/finding và đường tới hồ sơ nguồn.
- Làm màn hình checklist có số đo/đơn vị, lý do bỏ bước, nhiều finding và người theo dõi.
- Hiển thị hạn PM gốc/hạn điều chỉnh, finding còn mở và trạng thái chuyển thành ca sửa.
- Phối hợp A06 chạy job sinh kỳ bằng service identity. Thử chạy lại, kỳ quá hạn và xử lý bù có giới hạn.
- **Đạt khi** PM nhiều finding tạo đúng kỳ/WO, chạy job lại không sinh trùng, hoãn giữ hạn gốc và hoàn PM vẫn theo dõi được finding chưa xử lý.

### B06 — Dashboard và drill-down KPI · Bắt buộc

- Hiển thị SLA phản hồi/khôi phục, FTFR, PM và các chỉ số tài chính theo quyền có sẵn trong reporting.
- Luôn hiện kỳ, `as_of`, formula version, tử/mẫu, thiếu dữ liệu, cửa sổ FTFR và trạng thái provisional.
- Cho mở Request/WO/PM/hóa đơn nguồn theo quyền. Người không có quyền tài chính chỉ thấy tập thông tin được cấp.
- Chuẩn bị ca trễ, callback, thiếu mốc và đính chính muộn để kiểm số liệu, cùng Thành viên 3 đối chiếu phần tài chính.
- **Đạt khi** số trên UI khớp snapshot và chứng từ nguồn; revision mới giữ được snapshot cũ; số chưa đủ dữ liệu hiển thị rõ.
- **Phụ thuộc** dữ liệu B02/B05, tài chính C04 và quyền A02.

### B07 — Cảnh báo và notification có người nhận · Bắt buộc

- Triển khai thông báo trong app cho SLA sắp trễ/quá hạn, ETA vượt hẹn, PM tới hạn, finding quá hạn và hợp đồng sắp hết hiệu lực.
- Ngưỡng và người nhận lấy từ cấu hình/owner. Việc chờ khách/chờ hàng tiếp tục dùng policy SLA đã chốt.
- Job có khóa chống gửi trùng, kiểm scope người nhận, giới hạn nhắc lại và log kết quả. Email là kênh cấu hình thêm khi nhóm đã có SMTP để kiểm chứng.
- **Đạt khi** mỗi tình huống gửi tới đúng người; chạy lại không tạo bản trùng; khi hoàn tất/đổi owner thì lượt sau xử lý đúng trạng thái mới.
- **Phụ thuộc** A01/A02/A06; C03 cung cấp ETA có phiên bản và sự kiện thay đổi.

## 5. Người 3 — Thành viên 3 phụ trách kho, mua hàng, tài chính và tri thức

Phạm vi chính gồm M05, M06, M07 và M09. Làm kho/mua trước, sau đó tài chính và corpus tri thức. Có thể chuẩn bị tài liệu SOP sớm trong lúc chờ review code kho.

### C01 — Tồn khả dụng, giữ chỗ, bàn giao và trả hàng chưa dùng · Bắt buộc

- Làm màn hình theo item/kho/WO với actual, held, available, nơi giữ, lượng dùng và lượng còn giữ.
- Nối command reserve, transfer_reserved, consume và release hiện có. Trả hàng chưa dùng từ kho xe về kho tổng bằng chứng từ native có nguồn WO và lý do.
- Giữ tách bạch release reservation với chuyển vật tư vật lý. Dùng Stock Entry để phản ánh chuyển kho.
- **Đạt khi** ca kho tổng → xe → dùng một phần → trả phần thừa đối chiếu đúng Bin/ledger, retry không nhân chứng từ và invoice không xuất kho lần hai.
- **Phụ thuộc** A02 và phối hợp UI với B04.

### C02 — Reservation hết hạn, kho cách ly và kiểm kê · Bắt buộc

- Hiển thị giữ chỗ đã qua hạn và WO nguồn để thủ kho/điều phối xử lý. Mốc giờ hết hạn hiện chưa tự làm release, cần giữ chuyển trạng thái rõ ràng.
- Chốt với A01 cách xử lý giữ chỗ quá hạn. Nếu tự động release, dùng service identity, command idempotent và kiểm cạnh tranh với consume/transfer.
- Cấu hình nhận diện kho cách ly và kiểm phía server để hàng bị loại không được reserve/cấp cho ca qua các đường nghiệp vụ.
- Xây quy trình kiểm kê bằng Stock Reconciliation native với người duyệt, lý do, bằng chứng và kiểm tác động tới các hold đang mở.
- **Đạt khi** giữ chỗ quá hạn được xử lý theo chính sách, chặn dùng hàng cách ly, kiểm kê không làm tồn khả dụng cam kết vượt lượng cấp được và có audit quyết định.

### C03 — Giao thiếu, hàng lỗi, ETA và mua bù · Bắt buộc

- Thêm thao tác cập nhật ETA có actor/lý do, phản ánh lên nhu cầu và hàng đợi điều phối qua hợp đồng dữ liệu đã chốt.
- Hoàn thiện ca PO đã nhận đủ tổng số tốt + lỗi nhưng demand còn thiếu lượng dùng được. Phân biệt nhận hàng, chấp nhận sử dụng và hoàn thành nhu cầu.
- Thiết kế nhánh xử lý hàng bị loại qua chứng từ ERPNext phù hợp, trả NCC/nhận thay thế hoặc đơn mua bù. Lưu liên kết demand và các chứng từ cũ, hỗ trợ quan hệ nhiều chứng từ nếu cần.
- Hỗ trợ kết thúc phần nhu cầu còn lại có lý do/người duyệt. Chốt phạm vi với A01 trước khi sửa schema/unique key hiện có.
- **Đạt khi** ví dụ demand 5, có sẵn 1, mua 4, nhận 3 tốt + 1 lỗi vẫn phản ánh thiếu 1; nhánh mua bù/nhận thay thế đóng thiếu đúng, chạy lại không mua trùng.

### C04 — Đối soát chi phí, hóa đơn và công nợ · Bắt buộc

- Làm màn hình dự toán/phiên bản/duyệt và đối soát charge với giờ công, vật tư, bảo hành, goodwill và billable.
- Kiểm hiển thị số đã duyệt với khoản được lập hóa đơn. Dữ liệu cost/revenue theo quyền A02.
- Hoàn thiện ca lập invoice nháp → người có quyền submit native → nhận thanh toán qua Payment Entry native → xem số còn phải thu.
- Xử lý invoice nháp bị sửa/hủy bỏ trước submit để charge không bị kẹt allocation, có quyết định và lịch sử. Kiểm việc hủy invoice đã submit qua command manager.
- Chốt thuế/làm tròn và VND cho bản bàn giao. Các khoản thay đổi vượt nội dung duyệt quay lại quyết định dự toán đúng phiên bản.
- **Đạt khi** chứng minh một ca billable, một ca warranty/goodwill, invoice đã submit, thanh toán một phần/đủ và một ca hủy hợp lệ; ledger, charge và KPI tài chính khớp nguồn.
- **Phụ thuộc** A01/A02, phối hợp A03 cho khách duyệt và B06 cho KPI. Bộ nghiệm thu phải kiểm riêng invoice draft và submitted.

### C05 — UI kho/mua/kế toán và nghiệm thu trình duyệt · Bắt buộc

- Tối ưu các dialog native/SHD cho giữ hàng, nhận hàng, duyệt PO và đối soát, hiển thị trạng thái và chứng từ liên quan.
- Cùng B01 chạy các bước thuộc kho/mua/tài chính của ba luồng đã có trên trình duyệt.
- Kiểm Purchasing không tự duyệt PO khi thiếu role quản lý, thủ kho đúng phạm vi kho, kế toán đúng company/customer và nội dung PO đổi phải duyệt lại.
- **Đạt khi** người giữ đúng vai trò làm được công việc của họ bằng UI, từ chối đúng quyền và có ID chứng từ/ảnh hoặc video làm bằng chứng.

### C06 — Catalog SOP và bài học từ ca · Bắt buộc

- Làm giao diện tìm/lọc theo model, phiên bản, hiệu lực và trạng thái. Hiện reviewer và nguồn rõ ràng.
- Chuẩn bị ít nhất một model có SOP và lịch sử nhất quán để bàn giao AI-1. Tài liệu tổng hợp phải có nhãn minh họa và người review trong nhóm.
- Tạo bản nháp bài học từ WO đã hoàn thành, giữ liên kết `lesson_work_order`, bổ sung nguồn rồi qua reviewer publish/revoke. Kiểm quyền WO nguồn.
- Cùng A05 tạo câu hỏi có đáp án/nguồn kỳ vọng, ca khác khách, khác model, phiên bản hết hạn và nguồn mâu thuẫn.
- **Đạt khi** KTV tìm đúng tài liệu, bản draft/revoked/ngoài scope bị loại, phiên bản cũ vẫn truy được lịch sử theo quyền và AI-1 nhận corpus đúng.
- **Phụ thuộc** A02; có thể bắt đầu dữ liệu và câu hỏi trước khi UI catalog xong.

## 6. Nâng cấp đề xuất sau phạm vi bàn giao đầu tiên

Các task sau là backlog có chủ sở hữu. Nhóm chọn theo nhu cầu thực tế và thời gian còn lại. Mỗi lựa chọn cần bổ sung kiểm thử trạng thái, quyền và migration tương ứng.

| Task | Nâng cấp | Chủ trì | Phụ thuộc và tiêu chí chính |
|---|---|---|---|
| X01 | SLA pause có điều kiện, lịch cam kết nhiều cấp | Thành viên 2 | A01 chốt loại chờ được pause; giữ đủ lịch sử, xử lý giao ca/ngày nghỉ và KPI theo phiên bản policy. |
| X02 | Đổi phạm vi/generation WO khi đang làm hoặc sau nghiệm thu | Thành viên 2 | B03/B04, C04; phân tách phần đã thực hiện, phần thêm và duyệt phí mới, giữ booking/hold/charge nhất quán. |
| X03 | Chuyển site/ngừng máy, QR hồ sơ và PM theo đồng hồ chạy | Thành viên 2 | B05/A02; có lịch sử vị trí, quyền trước/sau chuyển, đúng thiết bị khi quét QR. Meter-based PM cần nguồn số đo và quy tắc kỳ. |
| X04 | Serial/batch, linh kiện tháo ra và core return | Thành viên 3 | C01/C02; dùng cơ chế native, phân biệt hàng mới/thu hồi, đối soát theo serial và người giữ. |
| X05 | Gom nhiều demand vào một MR/PO và phân bổ cung ứng | Thành viên 3 | C03; có allocation theo dòng, khóa cạnh tranh, không dùng cùng lượng cung để hứa cho hai ca. |
| X06 | Credit note, invoice nhiều lần, ngoại tệ | Thành viên 3 | C04/A01; chốt tỷ giá/thuế/cách phân bổ, số hoàn/thu và KPI truy đúng nguồn. |
| X07 | OCR PDF, chunk, hybrid retrieval và dẫn trang | Thành viên 3 | C06/A04; parser giữ số đo/đơn vị, index có phiên bản, kiểm thu hồi ngay cả khi index/cache chậm. |
| X08 | Agent tạo một loại chứng từ nháp có duyệt | Bạn | A04/A05, C03 hoặc C04; proposal/hash/expiry, duyệt đúng payload, revalidate, transaction receipt và kiểm crash/retry. |
| X09 | Durable run/checkpoint/resume và quan sát Harness đầy đủ | Bạn | A04; counters/phiên bản giữ qua restart, phân biệt outcome run với command, có fault injection và trace theo quyền. |
| X10 | Duyệt nhiều cấp/delegation, SSO và quản lý bí mật | Bạn | A02/A06, chính sách doanh nghiệp; ủy quyền có hạn/phạm vi, thu hồi có hiệu lực và audit đầy đủ. |
| X11 | Email/Zalo/hotline hoặc IoT | Bạn | Có tài khoản/kênh thử được phép sử dụng, A01/A02; inbound xác thực nguồn, chống nhận lặp và bảo vệ thông tin khách. |
| X12 | Mobile offline và tối ưu tuyến/điều phối | Thành viên 2 | B03/B04; đồng bộ có version/conflict, thuật toán dựa dữ liệu lịch/địa điểm đã xác nhận và đo lợi ích thực tế. |

Thiết kế production hiện có mô tả kiến trúc hạ tầng mục tiêu. A06 cần chọn cấu hình vận hành phù hợp nơi bàn giao Bench. Quy mô nhiều node/HA được bổ sung khi có yêu cầu tải và phục hồi được xác nhận.

## 7. Thứ tự làm để ba người triển khai song song

| Mốc | Bạn | Thành viên 2 | Thành viên 3 | Điều kiện chuyển mốc |
|---|---|---|---|---|
| 1 — Nền chung và phát hiện lỗi | A01, A02, dựng CI của A06; thử A04 với JSON mẫu | B01, mẫu B02/B03 | C05 khảo sát UI, C01; chuẩn bị corpus C06 | Chốt policy, API cần dùng, phân quyền và lỗi quan trọng của các luồng hiện tại. |
| 2 — Ba nhóm nghiệp vụ chạy trên UI | A03, API/quyền cần bổ sung, vận hành scheduler A06 | B02, B03, B04, B05 | C01, C02, C03 | Ca sửa/PM/vật tư chạy trên UI, gồm khách và người giữ đúng vai trò; ca sai quyền bị chặn. |
| 3 — Quyết toán, cảnh báo và AI | A04, A05; hoàn thành restore A06 | B06, B07 | C04, hoàn thành C05/C06 | Có invoice submit/thanh toán, KPI nguồn thật, cảnh báo đúng người và AI model thật có dẫn nguồn. |
| 4 — Bản phát hành | A07 và xử lý lỗi tích hợp | Nghiệm thu dịch vụ/KPI và tài liệu vai trò | Nghiệm thu kho/mua/tài chính/tri thức | Checklist cuối đạt, tồn đọng được ghi rõ, các task nâng cấp đã chọn có trạng thái cụ thể. |

Mỗi mốc có thể chia thành nhiều PR. Chỉ ghi thời lượng sau khi từng người đọc task và xác nhận khả năng thực hiện. Nếu một người bị dồn việc, chuyển task UI hoặc dữ liệu độc lập sang người đã hoàn thành mốc, giữ người sở hữu module review thay đổi.

## 8. Điểm nối và quy tắc phối hợp

### Hợp đồng cần thống nhất từ mốc 1

Xem contract IC-01 đến IC-08 và cổng nghiệm thu CT-01 đến CT-08 trong [contract tích hợp](contract_tich_hop_nhom_3_nguoi.md). Danh mục 40 command hiện có nằm ở phụ lục để giữ đúng tên và signature khi viết UI.

| Điểm nối | Bên cung cấp | Bên dùng | Nội dung cần chốt |
|---|---|---|---|
| Portal khách và quyết định chi phí | Thành viên 3 cung cấp dữ liệu dự toán; Bạn giữ API/quyền portal | Bạn, Thành viên 2 | ID/hash/phiên bản/hạn duyệt, số tiền và trạng thái thật. |
| ETA mua và thiếu vật tư | Thành viên 3 | Thành viên 2 | Demand/WO, số còn thiếu dùng được, ETA, thời điểm cập nhật và lý do. |
| Kho và thao tác KTV | Thành viên 3 | Thành viên 2 | Hold còn hiệu lực, kho giữ, lượng còn, visit, receipt sau consume/transfer/release. |
| KPI và tài chính | Thành viên 3, Bạn kiểm quyền | Thành viên 2 | Trạng thái invoice draft/submitted/cancelled, nguồn charge, cost thiếu và quyền đọc. |
| M09 và AI-1 | Thành viên 3 | Bạn | Model/version/hiệu lực/scope/source_reference, văn bản, giới hạn dữ liệu và cách thu hồi. |
| Notification và scheduler | Thành viên 2 viết nghiệp vụ job; Bạn cấu hình vận hành | Cả nhóm | Service identity, recipient scope, khóa chống trùng, ngưỡng và lỗi có thể retry. |

### Mã nguồn và môi trường

- Mỗi task dùng nhánh `codex/<ma-task>-<mo-ta>` từ `develop` đã cập nhật. Một PR tập trung vào một lát có thể review/nghiệm thu.
- Bạn điều phối thay đổi `schema.py`, generator DocType, hooks, permission, migration và runner chung. Chủ task đề xuất thay đổi trong PR để tích hợp theo thứ tự, không tự tạo hai định nghĩa cho cùng trường.
- Thành viên 2 giữ các màn hình dịch vụ/lịch/KPI. Thành viên 3 giữ màn hình kho/mua/tài chính/catalog. Bạn giữ portal khách và màn hình AI. Các thay đổi vào `public/js/operations.js` cần báo người còn lại trước khi ghép.
- UI kế thừa Frappe Desk và `DESIGN.md`. Mã được viết vào custom app và đưa qua Git; tùy chỉnh thực hiện trên site phải được xuất thành phần cài/migrate tái lập được.
- Mỗi người ưu tiên Bench/site riêng. Khi dùng Bench chung, xếp lượt chạy runner dựng site thử, thông báo tên site/cổng và tránh thay symlink app lúc người khác đang chạy.
- Bí mật model, token, mật khẩu DB và bản sao dữ liệu thật được giữ ngoài Git. Dữ liệu nghiệm thu dùng bản tổng hợp hoặc dữ liệu đã được phép sử dụng.
- PR ghi rõ thay đổi hành vi, dữ liệu cũ bị ảnh hưởng, ca kiểm thử đã chạy và phần còn mở. Người khác trong nhóm review trước khi người tích hợp ghép vào `develop`.

### Mẫu giao một task

```markdown
Task A01 / B01 / C01
Người phụ trách
Nhánh và PR
Đầu vào và phụ thuộc
Phạm vi làm trong PR
Quyết định nghiệp vụ cần chốt
Tiêu chí nghiệm thu lấy từ task
Ca thành công, ca từ chối và ca retry/cạnh tranh liên quan
Lệnh kiểm tra và kết quả
ID chứng từ, ảnh/video hoặc báo cáo bằng chứng
Tình trạng còn mở và người xử lý tiếp
```

## 9. Checklist nghiệm thu toàn chương trình

- [ ] Clone repo và dựng site thử từ trắng bằng runner, toàn bộ nhóm kiểm tra trả thành công.
- [ ] Nâng cấp từ dữ liệu ở mốc `d175103`, migrate lại và đọc/tiếp tục xử lý chứng từ cũ.
- [ ] Có cấu hình triển khai, ma trận quyền AIS/native và hướng dẫn tài khoản dịch vụ.
- [ ] Khách gửi yêu cầu, duyệt dự toán, theo dõi ETA và nghiệm thu trên portal.
- [ ] Điều phối triage/gán lịch, KTV thực hiện nhiều visit, ghi công/vật tư/file trên UI.
- [ ] Chứng minh phục hồi, nghiệm thu khách và đóng ca đúng trạng thái, gồm callback/đính chính.
- [ ] Kho giữ/bàn giao/dùng/trả/kiểm kê đối chiếu Bin và stock ledger, có ca cạnh tranh.
- [ ] Không cấp vật tư cách ly; reservation quá hạn được xử lý theo policy đã chọn.
- [ ] Mua nhận từng phần/hàng lỗi, cập nhật ETA và giải quyết được demand còn thiếu sau khi PO nhận đủ tổng lượng.
- [ ] Lập invoice nháp, submit native, nhận thanh toán và hủy hợp lệ có bằng chứng. Charge không bị tính trùng hoặc kẹt ở nháp bỏ dở.
- [ ] KPI mở được hồ sơ nguồn, giữ snapshot/revision và hiển thị dữ liệu thiếu, FTFR chưa đủ cửa sổ.
- [ ] Notification và PM/KPI scheduler chạy theo đúng scope, chạy lại không tạo tác động trùng.
- [ ] Tri thức publish/revoke có reviewer/nguồn; AI-1 đọc đúng model/quyền và trả lời có dẫn nguồn từ model thật.
- [ ] Ca sai quyền, hết hạn duyệt, payload đổi sau duyệt, token thu hồi và truy cập file/export đều được kiểm chứng.
- [ ] Backup khôi phục được DB, private files và cấu hình cần thiết trên site biệt lập.
- [ ] Có hướng dẫn vận hành theo vai trò, trình tự demo, giới hạn còn mở và danh sách nâng cấp nhóm đã chọn.

## 10. Tài liệu và mã đầu vào

- [README cài đặt và kiểm thử](../../README.md).
- [Ánh xạ 10 module, quy trình và giới hạn hiện tại](business_modules.md).
- [10 bản thiết kế module](../design/modules/).
- [Hợp đồng domain/workflow](../design/05_domain_workflow_contracts.md).
- [Mã custom app](../../apps/smart_helpdesk/smart_helpdesk/).
- [Bộ nghiệm thu vai trò và ba luồng nền](../../apps/smart_helpdesk/smart_helpdesk/tests/acceptance.py).
- [Runner Bench dựng site thử](../../scripts/tests/run_bench_checks.py).
- [API ERP context AI-1](ai1_erp_context.md) và [JSON mẫu](ai1_erp_context.example.json).
- [Kiến trúc Agent Harness](../design/ai_architecture/readme.md) và [gates nghiệm thu AI](../design/ai_architecture/08_observability_and_evaluation.md).
- [Design system của dự án](../../DESIGN.md).
