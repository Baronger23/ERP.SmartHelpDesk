# Phân tích doanh nghiệp, pain point và user story

## 1. Độ tin cậy của phân tích

Phân tích này là thiết kế trên bối cảnh AIS giả định đã được người dùng chọn, không phải biên bản khảo sát. Không có dữ liệu đo hiện trạng hoặc phỏng vấn xác nhận. Các pain point dưới đây là **giả thuyết có cơ chế gây tổn thất**, được suy ra từ việc doanh nghiệp B2B bán dịch vụ, quản lý nhiều khách/site và phải bàn giao giữa các bộ phận.

Đánh dấu nguồn: **H** = giả thuyết doanh nghiệp cần khảo sát; **R** = dấu hiệu trong repository; **D** = quyết định thiết kế đề xuất. Một pain point H có thể dẫn đến thiết kế mới dù chưa có R. Ngược lại, có script R không đủ lý do để thêm chức năng nếu không có giá trị doanh nghiệp.

Chuỗi suy luận: mục tiêu kinh doanh → điểm bàn giao/rủi ro → nguyên nhân thiếu kiểm soát → pain point → kết quả người dùng cần → năng lực/module → chức năng và dữ liệu → nghiệm thu. Các tính năng có cùng tên như “tự động phân công” có thể giải quyết vấn đề khác nhau; cần chỉ rõ chúng dùng kỹ năng, lịch và nguồn lực nào.

## 2. Bản đồ các giả thuyết pain point

| PP | Giả thuyết và nguyên nhân | Hệ quả cần kiểm chứng | Dấu hiệu/bằng chứng cần thu | Chủ trách nhiệm / module |
|---|---|---|---|---|
| PP-01 | Không có một hồ sơ liên hệ/site thống nhất; người gọi khác người duyệt phí | Báo nhầm máy, xin phép sai người | Ca phải gọi lại để tìm người xác nhận, site thiếu liên hệ | Quản lý khách / M01 |
| PP-02 | Quyền lợi/phạm vi thay đổi nhưng không có phiên bản theo ngày hiệu lực | Áp sai SLA, miễn phí sai hoặc bỏ sót quyền lợi | Hợp đồng, phụ lục và ca bị tranh chấp | Quản lý dịch vụ / M01 |
| PP-03 | Hotline/Zalo và nhập hệ thống là hai thời điểm khác nhau; thiếu chủ ca | Mất yêu cầu, khách chờ nhưng báo cáo không thấy | Nhật ký báo lỗi so với creation, ca không có owner | Điều phối / M02 |
| PP-04 | Mức ưu tiên dựa trên cảm giác; sự cố và yêu cầu trùng không được nhận diện | Dồn nguồn lực sai, tính deadline không nhất quán | Ca đổi priority nhiều lần, cùng máy nhiều yêu cầu | Điều phối / M02 |
| PP-05 | Chọn người chỉ theo lượt mà không biết khả dụng/kỹ năng/vật tư | Điều xe lại, chờ chuyên gia, trễ cam kết | Lịch, kỹ năng, lý do chuyển người và lượt đến | Điều phối / M03 |
| PP-06 | Một ticket gộp nhiều lần đến; thiếu kết quả thử máy và đồng ý khách | Không biết đã sửa dứt điểm; callback khó truy trách nhiệm | Work log, biên bản nghiệm thu, ca tái phát | Trưởng nhóm kỹ thuật / M03 |
| PP-07 | Hồ sơ máy chỉ là tên; thiếu cấu hình, serial, chủ sở hữu và lịch sử | Chọn sai phụ tùng/hướng dẫn, nhầm kế toán máy khách | Thời gian tìm máy, lỗi item/model và lịch sử chuyển site | Quản lý tài sản kỹ thuật / M04 |
| PP-08 | Lịch PM không phối hợp cửa sổ sản xuất; phát hiện lỗi chỉ nằm trong ghi chú | PM bị bỏ hoặc bất thường không có người theo tiếp | Kỳ quá hạn, lý do hoãn, phát hiện chưa đóng | Trưởng nhóm kỹ thuật / M04 |
| PP-09 | Tồn nhìn thấy chưa trừ giữ chỗ; nhiều ca dùng chung phụ tùng | Hứa cấp hàng nhưng hết khi tới kho | Yêu cầu giữ chỗ trùng, thiếu hàng sau phân công | Thủ kho / M05 |
| PP-10 | Chuyển lên xe bị coi là tiêu hao; vật tư thừa/hỏng không hoàn về sổ | Chênh kho, đội chi phí ca, không truy người giữ | Kiểm kê xe, phiếu chuyển/xuất/trả/thu hồi | Thủ kho và KTV / M05 |
| PP-11 | Mua chỉ nhìn tồn thực, không xét đơn mở và nhu cầu cam kết | Mua lặp hoặc mua quá muộn | MR/PO trùng, hàng dư, ca chờ theo item | Mua hàng / M06 |
| PP-12 | PO và nhận hàng không khớp dòng; nhận thiếu/sai được đánh dấu hoàn tất | Hàng chưa dùng được nhưng ca được hứa có vật tư | Lượng nhận thực, reject/return, ngày hẹn NCC | Mua hàng / M06 |
| PP-13 | Bảo hành được suy từ nhãn máy; phát sinh chưa có người duyệt | Tranh chấp phí và mất doanh thu | Khoản miễn phí, đồng ý thay đổi, hợp đồng áp dụng | Kế toán/quản lý dịch vụ / M07 |
| PP-14 | Công, vật tư, giảm trừ và giá vốn nằm rời rạc | Không hiểu lãi/lỗ ca, lập thiếu/trùng hóa đơn | Time log, ledger và dòng hóa đơn theo ca | Kế toán / M07 |
| PP-15 | KPI chỉ nhìn status hiện tại, thiếu thời gian chờ và cửa sổ quan sát | Ca trễ hoặc sửa lại bị che; so sánh sai nhóm khách | Deadline gốc, lịch sử, tập đủ dữ liệu và công thức | Quản lý dịch vụ / M08 |
| PP-16 | Báo cáo tổng hợp không quay về nguồn; lỗi dữ liệu không có người sửa | Không tin dashboard, ra quyết định chậm | Tỷ lệ mốc/liên kết thiếu, drill-down và xử lý lỗi | Data steward / M08 |
| PP-17 | Hướng dẫn nằm trong file/chat cá nhân và khác phiên bản máy | Tìm lâu, dùng SOP/model sai | Thời gian tìm tài liệu, nguồn được sử dụng | Trưởng nhóm kỹ thuật / M09 |
| PP-18 | Ca khó/tái phát không chuyển thành tri thức được duyệt | Lặp lại chẩn đoán sai; phụ thuộc người lâu năm | Bài học sau ca, người duyệt và lịch sử SOP | Trưởng nhóm kỹ thuật / M09 |
| PP-19 | Role rộng và tài khoản dùng chung; không giới hạn khách/ca/kho | Lộ dữ liệu, khó xác định người thay đổi | Ma trận quyền, truy cập trái phạm vi, tài khoản nghỉ việc | Quản trị / M10 |
| PP-20 | Ngoại lệ như miễn phí, hủy hoặc sửa giờ không có phê duyệt/audit | Không phân định trách nhiệm, dữ liệu bị hợp thức hóa | Các quyết định ngoại lệ, nhật ký và phục hồi | Quản lý và quản trị / M10 |

Tất cả PP hiện là H. R nổi bật: mã đã có liên kết kho-ca, incident_time, role, SLA và KPI nhưng thiếu một số kiểm chứng; R chỉ giúp xác định khoảng cách triển khai. Không công bố doanh nghiệp “đang gặp” các vấn đề này như kết luận khảo sát.

## 3. Danh mục user story và truy vết chức năng

Mỗi story được viết theo kết quả, không theo nút bấm. Tiêu chí BDD và ngoại lệ nằm tại module được liên kết. Mỗi mã US có nhóm tiêu chí `AC-xx.*` cùng số.

| US | Là ai, muốn gì, để làm gì? | PP | Chức năng / module |
|---|---|---|---|
| US-01 | Quản lý khách muốn một hồ sơ khách/site/liên hệ để tiếp nhận và xin xác nhận đúng người | 01 | M01-F01/F02 |
| US-02 | Quản lý dịch vụ muốn xác định máy/phạm vi đang được phục vụ để không hứa vượt hợp đồng | 02 | M01-F03 |
| US-03 | Điều phối muốn quyền lợi theo ngày báo lỗi để áp cam kết nhất quán | 02 | M01-F04/F05 |
| US-04 | Quản lý khách muốn cảnh báo hợp đồng sắp hết/đổi phạm vi để không gián đoạn phục vụ | 02 | M01-F06 |
| US-05 | Người báo lỗi muốn báo đúng máy và nhận mã theo dõi để không phải nhắc lại thông tin | 03 | M02-F01 |
| US-06 | Điều phối muốn lưu giờ báo và nhận diện yêu cầu trùng để không mất ca hoặc đếm sai | 03/04 | M02-F02/F03 |
| US-07 | Điều phối muốn đánh giá ảnh hưởng và hạn theo cam kết để ưu tiên đúng việc | 04 | M02-F04/F05 |
| US-08 | Khách/quản lý muốn biết ca chờ gì và nguy cơ trễ để thống nhất bước tiếp theo | 03/04 | M02-F06 |
| US-09 | Điều phối muốn work order/lượt đến rõ ràng để giao đủ gói việc và theo dõi thực hiện | 05/06 | M03-F01 |
| US-10 | Điều phối muốn chọn người theo kỹ năng, lịch và vật tư để giảm chuyến đi không giải quyết được | 05 | M03-F02/F03 |
| US-11 | KTV muốn ghi chẩn đoán, công và bằng chứng để nghiệm thu và đối soát đúng | 06 | M03-F04/F05 |
| US-12 | Trưởng nhóm muốn nối ca tái phát và quyết định trách nhiệm để cải thiện chất lượng | 06 | M03-F06 |
| US-13 | KTV muốn hồ sơ máy/serial/model và lịch sử để chẩn đoán đúng thiết bị | 07 | M04-F01/F02 |
| US-14 | Người lập PM muốn checklist theo loại máy và cửa sổ vận hành để kế hoạch thực hiện được | 08 | M04-F03/F04 |
| US-15 | KTV muốn ghi thông số/kết quả và chuyển bất thường có owner để không bỏ phát hiện | 08 | M04-F05 |
| US-16 | Quản lý muốn lịch sử chuyển site/ngừng máy và thay đổi kế hoạch để dữ liệu không bị mất | 07/08 | M04-F06 |
| US-17 | Điều phối/thủ kho muốn lượng khả dụng và giữ chỗ theo ca để không hứa vượt vật tư | 09 | M05-F01/F02 |
| US-18 | Thủ kho muốn bàn giao giữa kho tổng/xe bằng chứng từ để biết người đang giữ hàng | 10 | M05-F03 |
| US-19 | KTV muốn ghi dùng, thừa và hỏng theo ca để tiêu hao phản ánh thực tế | 10 | M05-F04/F05 |
| US-20 | Thủ kho muốn kiểm kê và đối soát chênh lệch có duyệt để kho có thể tin cậy | 09/10 | M05-F06 |
| US-21 | Mua hàng muốn xét nhu cầu và đơn mở để bổ sung đúng lượng, không mua lặp | 11 | M06-F01/F02 |
| US-22 | Người duyệt muốn thấy nguồn nhu cầu và lựa chọn NCC để chấp thuận mua có căn cứ | 11 | M06-F03 |
| US-23 | Mua hàng/thủ kho muốn nhận theo dòng và xử lý thiếu/sai để biết hàng thật có dùng được không | 12 | M06-F04/F05 |
| US-24 | Điều phối muốn ETA và đơn chậm được cập nhật để hẹn khách trung thực | 12 | M06-F06 |
| US-25 | Kế toán muốn chính sách phí theo phạm vi/nguyên nhân để xác định phần AIS và khách chịu | 13 | M07-F01 |
| US-26 | Người duyệt phía khách muốn chấp nhận thay đổi giá/phạm vi trước khi làm để tránh tranh chấp | 13 | M07-F02 |
| US-27 | Kế toán muốn đối soát công/vật tư và lập hóa đơn nối ca để không bỏ sót/tính trùng | 14 | M07-F03/F04 |
| US-28 | Quản lý/kế toán muốn điều chỉnh phí và xem trạng thái phải thu để quyết toán có lịch sử | 13/14 | M07-F05/F06 |
| US-29 | Điều phối/quản lý muốn dashboard ca cần hành động để xử lý trước khi trễ | 15 | M08-F01 |
| US-30 | Quản lý kỹ thuật muốn SLA/FTFR/PM có định nghĩa để đánh giá chất lượng công bằng | 15 | M08-F02/F03 |
| US-31 | Quản lý muốn chi phí ca/máy/hợp đồng và thiếu vật tư để điều chỉnh năng lực phục vụ | 15/16 | M08-F04 |
| US-32 | Data steward muốn drill-down và danh sách lỗi dữ liệu để sửa nguồn, không sửa số tổng | 16 | M08-F05/F06 |
| US-33 | KTV muốn tìm SOP theo model/phiên bản để dùng hướng dẫn phù hợp | 17 | M09-F01/F02 |
| US-34 | Trưởng nhóm muốn duyệt bài học từ ca để kiến thức tái sử dụng đáng tin cậy | 18 | M09-F03 |
| US-35 | KTV muốn trợ lý trả lời có nguồn và biết khi thiếu căn cứ để không dùng lời đoán | 17 | AH-F04; M09-F05/F06 cung cấp evidence |
| US-36 | KTV muốn hỏi dữ liệu động/tạo đề nghị bằng tool có quyền để giảm thao tác lặp | 17/18 | AH-F05/F07; gateway/module nguồn |
| US-37 | Quản trị muốn tài khoản cá nhân và phạm vi role để truy trách nhiệm từng hành động | 19 | M10-F01/F02 |
| US-38 | Quản lý muốn phê duyệt ngoại lệ theo mức/thẩm quyền để tránh vượt quyền | 20 | M10-F03 |
| US-39 | Người kiểm soát muốn audit và chất lượng dữ liệu để phát hiện thay đổi bất hợp lý | 19/20 | M10-F04/F05 |
| US-40 | Quản trị muốn phục hồi và thu hồi quyền đúng quy trình để duy trì tính liên tục | 19/20 | M10-F06 |

## 4. Story map theo hành trình và mức ưu tiên

| Hoạt động | Tối thiểu xuyên suốt P1 | Hoàn thiện vận hành P2 | Nâng cấp có điều kiện P3 |
|---|---|---|---|
| Xác lập cam kết | Khách/site, phạm vi và bản cam kết áp dụng | Phụ lục, gia hạn, nhiều lịch/hợp đồng | Dự báo gia hạn, tích hợp CRM |
| Báo và phân loại | Nhập hộ/portal đơn giản, mốc thực, triage, hạn | Hợp nhất trùng và timeline chờ | Tự động tiếp nhận kênh ngoài |
| Chuẩn bị và thực hiện | WorkSource/work order/lượt, gán theo kỹ năng, reservation atomic, kết quả | Khả dụng lịch sâu, nhiều người, callback review sâu | Tối ưu tuyến, offline |
| Bảo trì phòng ngừa | Checklist và lần PM theo lịch | Cửa sổ hoãn, phân loại bất thường | Theo đồng hồ sử dụng/IoT khi đủ dữ liệu |
| Vật tư và mua | Reservation atomic, cấp/tiêu hao, MR-PO-PR có liên kết | Bàn giao/nhận thiếu/trả/kiểm kê sâu | Tối ưu tồn theo độ quan trọng/lead time |
| Phí và cải tiến | Approval phát sinh tối thiểu bind version/hash, phí/công/vật tư, báo cáo nguồn | Approval nhiều cấp/delegation và dispute sâu | Phân tích dự báo |

P1 là lát cắt domain có kiểm soát, không nghĩa mọi story đã triển khai. Approval phát sinh và reservation atomic bắt buộc P1 theo [hợp đồng chuẩn](05_domain_workflow_contracts.md). AI có lộ trình A1 read-only/A2 approved draft/A3 pilot riêng, với US-35/36 và US-41–48; không mặc định đẩy toàn bộ Agent Harness sang P3. US-33/34 tri thức vẫn hoạt động độc lập.

### User story Agent Harness bổ sung

| US | Nhu cầu / giá trị | PP | Năng lực và oracle |
|---|---|---|---|
| US-41 | Điều phối đề nghị triage/ca liên quan có nguồn | 03/04 | AH-F01/F02/F04; AC-41.* |
| US-42 | KTV tổng hợp SOP/lịch sử đúng model, biết conflict | 05/06/17 | AH-F02/F04, M09-F05/F06; AC-42.* |
| US-43 | Điều phối đề nghị KTV/slot theo kỹ năng/lịch/SLA | 05 | AH-F02/F05, M03; AC-43.* |
| US-44 | KTV kiểm tương thích/tồn và chuẩn bị vật tư | 09/10/17 | AH-F03/F05/F07, M04/M05; AC-44.* |
| US-45 | Mua hàng xét demand/PO mở, không tạo MR lặp | 11/12 | AH-F03/F05/F06, M06; AC-45.* |
| US-46 | Trưởng nhóm tổng hợp finding, đề nghị việc đúng WorkSource | 08 | AH-F02/F05/F07, M04/M03; AC-46.* |
| US-47 | Kế toán đọc coverage/charge và đề nghị xử lý lỗi phí | 13/14 | AH-F04/F05, M01/M07; AC-47.* |
| US-48 | Quản lý phân tích ca trễ/callback/chờ có kỳ và nguồn | 15/16 | AH-F02/F04/F08, M08; AC-48.* |

Giới hạn hành động và acceptance BDD: [E2E agent scenarios](ai_architecture/09_end_to_end_agent_scenarios.md). Những story AI hỗ trợ quyết định, không cấp quyền bypass phê duyệt hoặc tạo facts kỹ thuật.

## 5. Yêu cầu phi chức năng xuất phát từ tình huống vận hành

| Mã | Tình huống | Yêu cầu mục tiêu | Phép kiểm chứng |
|---|---|---|---|
| NFR-01 | Khách khác tổ chức/site | Kiểm tra truy cập cả UI, API, tìm kiếm, export và tệp | Thử đọc/sửa ID ngoài phạm vi và truy đường dẫn tệp |
| NFR-02 | Bấm lại sau mạng chậm | Tạo/submit có khóa chống trùng, kết quả rõ ràng | Gửi cùng request hai lần; chỉ một side effect |
| NFR-03 | Hai ca đòi cùng một phụ tùng | Giữ chỗ/tiêu hao không vượt lượng khả dụng | Hai yêu cầu đồng thời; chỉ lượng cho phép được xác nhận |
| NFR-04 | Hợp đồng/chính sách thay đổi | Version và snapshot quyền lợi/deadline của ca | Sửa hợp đồng; deadline gốc của ca cũ không đổi im lặng |
| NFR-05 | Mạng hiện trường gián đoạn | Biết dữ liệu đã lưu/chưa lưu; retry an toàn | Ngắt kết nối khi gửi; không báo thành công giả |
| NFR-06 | Báo cáo nhiều trang/đơn vị | Phân trang, filter và thời điểm dữ liệu nhất quán | Tập hơn giới hạn API, hai công ty và ca ngoài kỳ |
| NFR-07 | Người đổi việc hoặc nghỉ | Thu hồi tài khoản/token/phạm vi; bàn giao ca còn mở | Quyền cũ bị từ chối và ca vẫn có owner mới |
| NFR-08 | Lỗi vận hành/dữ liệu | Backup/restore và phát hiện dữ liệu thiếu liên kết | Khôi phục thử, kiểm tra số chứng từ và tham chiếu |

RPO/RTO, thời gian phản hồi màn hình và tải đồng thời chưa có số được xác nhận. Đề xuất đo nhu cầu trong khảo sát rồi đặt mục tiêu; không tự tuyên bố chuẩn enterprise bằng một tỷ lệ uptime.

## 6. Kế hoạch xác nhận với doanh nghiệp

Phỏng vấn người báo lỗi, điều phối, KTV, thủ kho, mua hàng và kế toán về 5-10 ca gần nhất theo cả thành công và thất bại; kiểm tra hồ sơ hợp đồng/phát sinh/ca tái phát tương ứng. Dùng số ca là đề xuất mẫu khảo sát, không phải dữ liệu đã thu.

Các câu hỏi cần chốt: ai được nhận/duyệt yêu cầu; SLA phản hồi khác thời điểm đến hiện trường thế nào; cam kết tính theo giờ phục vụ hay liên tục; có tạm dừng SLA khi chờ khách/vật tư không; khôi phục tạm có tính hoàn tất không; callback xác định theo triệu chứng hay nguyên nhân; vật tư nào cần serial/thu hồi; ai duyệt goodwill và phát sinh; PM được hoãn đến khi nào; dữ liệu nào khách được xem.

Sau khảo sát, mỗi PP nhận trạng thái confirmed/rejected/needs evidence, mức tác động và baseline. PP bị bác bỏ phải kéo theo điều chỉnh module/chức năng; không giữ tính năng chỉ vì đã có script.
