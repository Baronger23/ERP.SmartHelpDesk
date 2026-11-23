# AI-1 · Ngữ cảnh ERP cho US-42

API cung cấp hồ sơ máy, lịch sử công việc và SOP cho trợ lý kỹ thuật chỉ đọc. Phần tích hợp agent còn gồm gọi model, chọn bằng chứng từ ngữ cảnh và tổng hợp câu trả lời.

## Gọi API

```http
POST /api/method/smart_helpdesk.ai_context.get_context
Content-Type: application/json
```

```json
{
  "equipment_code": "ACC-EQ-001",
  "question": "Máy ACC-R1 rung cao. SOP và lịch sử ca trước ghi nhận gì?"
}
```

Dùng phiên Frappe của kỹ thuật viên (kèm CSRF cho POST) hoặc API token của chính kỹ thuật viên đó ở môi trường kiểm thử. ERP lấy danh tính từ phiên xác thực, dùng vai trò `AIS Field Technician` và kiểm phạm vi đọc trên từng loại hồ sơ. Mã máy là mã nghiệp vụ `equipment_code`. Gửi mã dài 1–140 ký tự và câu hỏi dài 1–1000 ký tự, tính sau khi bỏ khoảng trắng ở hai đầu.

Phản hồi nằm trong `message` của Frappe. [Mẫu JSON cho phần agent](ai1_erp_context.example.json) chứa cặp yêu cầu/phản hồi với ID minh họa. Khi chạy thật, lấy ID từ chính phản hồi đó.

| Trường | Ý nghĩa |
|---|---|
| `contract_version`, `observed_at`, `question` | Phiên bản hợp đồng `1.0`, thời điểm truy xuất UTC, câu hỏi để agent tổng hợp. Các timestamp nghiệp vụ của DocType theo giờ site Frappe. |
| `equipment` | Máy đang hoạt động, xác định bằng mã, kèm model/serial và phạm vi công ty/khách/site. |
| `history.work_orders`, `history.findings` | Công việc đi từ WorkSource của đúng máy qua Incident, Request hoặc kỳ PM, cùng finding của máy. Chỉ lấy công việc KTV được quyền đọc theo phân công. Trạng thái, phạm vi và kết quả visit được trả riêng. |
| `knowledge` | SOP/lesson trong catalog M09 đã công bố, còn hiệu lực, đúng model/khách và trong quyền đọc tri thức. SOP ở phạm vi toàn khách chỉ xuất hiện khi grant cho phép đọc bản đó. Dữ liệu là văn bản và metadata của catalog. |

Mỗi danh sách trả tối đa 5 mục và cờ `has_more`. Work order/finding sắp theo thời điểm tạo, visit theo thời điểm bắt đầu và SOP theo ngày bắt đầu hiệu lực, đều mới trước. SOP trả tối đa 8.000 ký tự với cờ `content_truncated` riêng. Câu hỏi được chuyển cho agent. ERP chọn tập nguồn theo máy, trạng thái và quyền, dùng thứ tự trên cho mọi câu hỏi.

Khi dẫn nguồn, giữ `doctype`, `name`, `revision`. Với SOP, dẫn thêm `document_version` và `source_reference`. Chỉ lấy phần văn bản hỗ trợ nhận định. Agent xử lý nội dung SOP và ghi chú hiện trường như dữ liệu bằng chứng. Chúng không cấp quyền hay điều khiển công cụ. Với danh sách rỗng, dữ liệu bị cắt hoặc nguồn mâu thuẫn, agent nêu rõ giới hạn và trả phần có căn cứ. Kết quả visit và finding là ghi nhận của ca trước. Chúng có thể hỗ trợ một giả thuyết về ca hiện tại.

HTTP 403 dùng chung cho mã máy ngoài quyền, mã không tồn tại và máy đã ngừng hoạt động. Payload thiếu/không hợp lệ bị từ chối. Nếu thấy lỗi từ ERP, agent cần báo không truy xuất được bằng chứng trong lượt đó. Một danh sách rỗng trong HTTP 200 nghĩa là lượt đọc đã thành công và không có mục phù hợp trong phạm vi đọc hiện tại.

## Chạy ca mẫu trên Bench

Trong WSL/Linux, từ thư mục repo chạy `python3 scripts/tests/run_bench_checks.py`. Runner dựng lại site thử và chạy ca US-42 ngay sau bộ nghiệm thu theo vai trò. Ca mẫu dùng `ACC-EQ-001`, model `ACC-R1`, lịch sử ca sửa và PM của khách A, cùng SOP tổng hợp đã duyệt qua lệnh nghiệp vụ. Các bản khác model/khách, draft, hết hạn, chưa đến hiệu lực và đã thu hồi làm dữ liệu đối chứng.

Mục `live_ai1_erp_context` trong báo cáo ghi kiểm tra HTTP bằng tài khoản KTV A/B, khách hàng và Guest. Cùng một model có dữ liệu ở hai khách để kiểm tra cách ly. Dữ liệu được tạo trên site thử và có nội dung minh họa.
