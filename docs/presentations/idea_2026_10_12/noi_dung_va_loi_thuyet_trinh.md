# Kịch bản thuyết trình ý tưởng Smart HelpDesk & Maintenance

12 slide · khoảng 11 phút 40 giây · khổ 16:9 · logo Bách khoa góc trên bên phải trên mọi trang.

## 01. Smart HelpDesk & Maintenance

Thời lượng: 30 giây.

### Nội dung trên slide

- Quản lý dịch vụ bảo trì công nghiệp B2B
- Kết nối yêu cầu, tác nghiệp, vật tư và chi phí
- Hỗ trợ nhân viên bằng AI Agent và tri thức kỹ thuật

### Lời thuyết trình

Dự án hướng tới doanh nghiệp cung cấp dịch vụ bảo trì cho nhiều nhà máy. Ý tưởng là quản lý xuyên suốt một ca dịch vụ, đồng thời hỗ trợ nhân viên tìm thông tin và chuẩn bị quyết định bằng AI. Bài trình bày đi từ bài toán doanh nghiệp đến kiến trúc nghiệp vụ, dữ liệu, AI và cách triển khai.

Nguồn: docs/design/00_tong_quan_he_thong.md

## 02. Bài toán phối hợp trong một ca bảo trì

Thời lượng: 60 giây.

### Nội dung trên slide

- Thông tin và cam kết chưa rõ
- Cần đúng người, đúng lịch và đủ phụ tùng
- Kết quả sửa phải nối với nghiệm thu và chi phí

### Lời thuyết trình

AIS là bối cảnh giả định của một doanh nghiệp bảo trì công nghiệp B2B. Khó khăn không chỉ là ghi nhận máy hỏng. Một ca đi qua điều phối, kỹ thuật viên, kho, mua hàng và kế toán. Khi thông tin không được bàn giao đầy đủ, doanh nghiệp có thể đi lại nhiều lần, trễ cam kết hoặc tranh chấp phí. Ví dụ: máy dừng, khách báo lỗi, kỹ thuật viên đến rồi phát hiện thiếu phụ tùng và khoản chi phí cần khách duyệt. Đây là giả thuyết thiết kế cần kiểm chứng, không phải kết quả khảo sát thực tế.

Nguồn: docs/design/01_phan_tich_doanh_nghiep_va_yeu_cau.md

## 03. Ý tưởng quản lý dịch vụ xuyên suốt

Thời lượng: 55 giây.

### Nội dung trên slide

- Yêu cầu có phạm vi, trách nhiệm và thời hạn
- Công việc, vật tư, chi phí liên kết theo ca
- Kết quả có bằng chứng để nghiệm thu và cải tiến

### Lời thuyết trình

Từ nhu cầu doanh nghiệp, hệ thống được tổ chức thành các nhóm năng lực nghiệp vụ. Mỗi yêu cầu có phạm vi, người chịu trách nhiệm và thời hạn. Công việc, vật tư và chi phí được liên kết theo ca. Khách muốn biết tiến độ và khoản phí cần duyệt; kỹ thuật viên cần hồ sơ máy, tài liệu và phụ tùng phù hợp; quản lý muốn biết ca nào đang vướng và vì sao. Mục tiêu là giúp mọi người nhìn cùng một quá trình và biết bước tiếp theo thuộc trách nhiệm của ai.

Nguồn: docs/design/00_tong_quan_he_thong.md

## 04. Tổng quan năng lực của hệ thống

Thời lượng: 75 giây.

### Nội dung trên slide

- Người dùng theo vai trò
- Mười module nghiệp vụ
- AI và quản trị xuyên suốt

### Lời thuyết trình

Đọc hình từ trên xuống: người dùng, kênh truy cập, nghiệp vụ, AI và kiểm soát, dữ liệu nền tảng. M01–M02 quản lý cam kết và tiếp nhận; M03–M04 tác nghiệp và thiết bị; M05–M07 vật tư, mua hàng và tài chính; M08–M10 báo cáo, tri thức và quản trị. Các module là những nhóm trách nhiệm trong cùng hệ thống, không có nghĩa mười ứng dụng độc lập. M09 cung cấp tri thức, Harness điều hành nhiệm vụ AI. Phạm vi đầu tiên là web responsive; ứng dụng di động riêng và tích hợp tự động là định hướng khi có triển khai.

Nguồn: docs/design/system-architeture.png

## 05. Cam kết, tiếp nhận và chuẩn bị

Thời lượng: 65 giây.

### Nội dung trên slide

- Khách, máy và quyền lợi
- Sự cố hoặc kỳ PM đến hạn
- Người, lịch và vật tư

### Lời thuyết trình

Phần đầu của luồng bắt đầu bằng hồ sơ máy, địa điểm và cam kết với khách. Có hai nguồn nhu cầu chính: khách yêu cầu xử lý và công việc bảo trì theo lịch. Cả hai cần nguồn việc rõ ràng để điều phối, nhưng kỳ PM không bắt buộc tạo sự cố. Trước khi hứa thực hiện, cần xác minh người có năng lực, lịch phù hợp và vật tư khả dụng. Có người được phân công chưa đủ để bảo đảm ca thực hiện được.

Nguồn: docs/design/system-logic.png

## 06. Thực hiện, nghiệm thu và cải tiến

Thời lượng: 65 giây.

### Nội dung trên slide

- Duyệt phát sinh trước khi làm
- Ghi công, vật tư và kết quả thực tế
- Nghiệm thu khác quyết toán

### Lời thuyết trình

Trong quá trình thực hiện, phạm vi hoặc chi phí có thể thay đổi. Phần vượt cam kết phải được duyệt trước khi làm. Một ca có thể cần nhiều lượt đến, nên giữ công, vật tư và kết quả từng lượt. M03 ghi nhận khôi phục và nghiệm thu; M02 sử dụng facts đó để đóng yêu cầu theo điều kiện; M07 đối soát và lập hóa đơn. Máy đã chạy lại, khách đã nghiệm thu, đã lập hóa đơn và đã thanh toán là những mốc riêng. Báo cáo và tri thức dùng kết quả có nguồn để cải tiến.

Nguồn: docs/design/system-logic.png

## 07. Dữ liệu theo dõi đúng công việc

Thời lượng: 65 giây.

### Nội dung trên slide

- Yêu cầu khác sự cố
- Lệnh công việc khác lần tác nghiệp
- Công, vật tư và phí có nguồn

### Lời thuyết trình

Đây là mô hình dữ liệu khái niệm, không cần đọc từng trường PK/FK. Hai người báo cùng một máy hỏng không nhất thiết tạo hai sự cố. Một nguồn công việc có thể sinh lệnh việc và mỗi lệnh có nhiều lượt thực hiện. Snapshot giữ quyền lợi áp dụng tại thời điểm tiếp nhận; PM có kỳ và phát hiện riêng. Công và vật tư tạo nguồn đối soát phí. Việc phân biệt các đối tượng giúp tránh đếm trùng, mất lịch sử và tính sai chi phí. Ảnh vẫn có một số nhãn v2.0; phần trình bày đối chiếu với tài liệu thiết kế hiện tại.

Nguồn: docs/design/data-architecture.png

## 08. AI hỗ trợ tra cứu và chuẩn bị quyết định

Thời lượng: 60 giây.

### Nội dung trên slide

- RAG tìm tài liệu có nguồn
- Tool lấy dữ liệu ERP hiện tại
- Agent phối hợp các bước

### Lời thuyết trình

Kỹ thuật viên có thể hỏi: máy này từng gặp lỗi tương tự chưa, tài liệu hướng dẫn kiểm tra gì và phụ tùng phù hợp còn không? RAG tìm tài liệu đúng model và dẫn nguồn. Tool ERP đọc lịch sử, quyền lợi và tồn khả dụng. Agent phối hợp các bước, đánh giá kết quả và hỏi thêm nếu thiếu dữ liệu. Nếu API kho lỗi, câu trả lời là chưa xác nhận được tồn, không được suy ra bằng không. Giá trị hướng tới là giảm thời gian tìm kiếm và chuẩn bị quyết định có căn cứ; chưa có số phần trăm cải thiện thực tế.

Nguồn: docs/design/ai_architecture/09_end_to_end_agent_scenarios.md

## 09. Agent Harness điều hành AI có kiểm soát

Thời lượng: 85 giây.

### Nội dung trên slide

- Lập kế hoạch, gọi tool, kiểm chứng
- Lưu tiến độ và chờ duyệt
- Đọc, đề xuất và dự thảo đã duyệt

### Lời thuyết trình

LLM hỗ trợ suy luận và diễn giải. Harness quản lý các bước thực hiện, quyền gọi công cụ và kết quả. M09 cung cấp tri thức; M10 và ERP giữ quyết định phê duyệt chính thức. Nhiệm vụ có thể lưu checkpoint và chờ người duyệt, rồi kiểm tra lại dữ liệu và quyền trước khi tiếp tục. Baseline gồm đọc, chuẩn bị đề xuất và ghi dự thảo đã được duyệt. Agent không tự giữ hàng thực, submit chứng từ, ép phân công hoặc đóng ca. Quan sát runtime AI là năng lực của Harness, khác M08 báo cáo nghiệp vụ; nhãn M08 ở khối quan sát trong ảnh không được dùng làm ranh giới module mới. Ứng dụng di động riêng là định hướng. Hình v2.0 được giải thích theo thiết kế hiện tại.

Nguồn: docs/design/ai-agent-architecture.png

## 10. Triển khai ERP và AI theo trách nhiệm

Thời lượng: 65 giây.

### Nội dung trên slide

- Truy cập theo vai trò
- ERP nghiệp vụ, AI hỗ trợ
- Dữ liệu riêng và vận hành có kiểm soát

### Lời thuyết trình

Đọc hình theo ba phần: truy cập, ứng dụng ERP/AI, dữ liệu và vận hành. ERPNext/Frappe là nền tảng nghiệp vụ. AI chạy ở nhóm thành phần riêng và truy cập ERP qua gateway, không đọc thẳng database nghiệp vụ. Các kho dữ liệu được đặt trong vùng riêng; vận hành có giám sát, secrets và sao lưu. Khi AI không sẵn sàng, nhân viên vẫn tiếp tục xử lý trên ERP. Đây là topology production mục tiêu, không phải hạ tầng đã chạy. Số instance trong hình là cấu hình khởi điểm đề xuất và cần điều chỉnh theo tải.

Nguồn: docs/design/deployment-architecture.png

## 11. Ưu tiên một ca dịch vụ hoàn chỉnh

Thời lượng: 45 giây.

### Nội dung trên slide

- Dữ liệu, quyền và ca xuyên suốt
- PM, vật tư và quyết toán
- Tri thức và AI có kiểm chứng

### Lời thuyết trình

Nhóm ưu tiên một ca từ tiếp nhận đến nghiệm thu và quyết toán, có nhánh thiếu vật tư hoặc phát sinh. Bước đầu chuẩn hóa dữ liệu và quyền; sau đó kết nối bảo trì, vật tư và nguồn phí. AI được bổ sung khi tài liệu và dữ liệu đủ tin cậy. Đã có nền tảng ERP và bộ thiết kế; các workflow mở rộng cùng tích hợp Agent cần triển khai và kiểm chứng thực. Giá trị được đánh giá qua thời gian xử lý, tính đầy đủ dữ liệu và khả năng truy nguyên kết quả, không dùng tỷ lệ demo để kết luận.

Nguồn: docs/design/03_lo_trinh_va_doi_chieu.md

## 12. Giá trị hướng tới của dự án

Thời lượng: 30 giây.

### Nội dung trên slide

- Khách theo dõi được dịch vụ
- Nhân viên có thông tin để phối hợp
- Quản lý có căn cứ để cải tiến

### Lời thuyết trình

Điểm chính của dự án là kết nối thông tin và trách nhiệm trong toàn bộ dịch vụ bảo trì. Khách hàng theo dõi được dịch vụ, nhân viên có thông tin để phối hợp và quản lý có căn cứ để cải tiến. AI hỗ trợ tìm hiểu và chuẩn bị hành động trong quy trình có kiểm soát. Xin cảm ơn thầy và mời trao đổi về ý tưởng, phạm vi cũng như hướng triển khai của nhóm.

Nguồn: docs/design/00_tong_quan_he_thong.md

