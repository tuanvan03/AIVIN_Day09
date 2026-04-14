# Routing Decisions Log — Lab Day 09

**Nhóm:** Nhóm-03-E402  
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `retrieval keyword matched ('p1').`  
**MCP tools được gọi:** Không có (mcp_tools_used: [])  
**Workers called sequence:** retrieval_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): SLA xử lý ticket P1 bao gồm: Phản hồi ban đầu (15p), Xử lý (4h), Escalation (10p), Stakeholder update (mỗi 30p).
- confidence: 1.0
- Correct routing? Yes 

**Nhận xét:** _(Routing này đúng hay sai? Nếu sai, nguyên nhân là gì?)_
- Routing này hoàn toàn chính xác. Hệ thống đã nhận diện được từ khóa "P1" và điều hướng sang retrieval_worker để truy xuất dữ liệu từ file tài liệu nội bộ support/sla-p1-2026.pdf. Kết quả trả về đầy đủ và chính xác theo yêu cầu.

_________________

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `policy keyword matched ('hoàn tiền'). Choosed MCP search_kb. Didn't choose MCP get_ticket_info.`  
**MCP tools được gọi:** search_kb  
**Workers called sequence:** policy_tool_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng (kèm các điều kiện về lỗi NSX và seal).
- confidence: 0.85
- Correct routing? Yes

**Nhận xét:**
- Supervisor đã nhận diện đúng ý định hỏi về chính sách (policy) thông qua từ khóa "hoàn tiền". Việc chọn policy_tool_worker là chính xác vì cần kiểm tra các quy tắc và ngoại lệ (như Flash Sale) trong tài liệu policy/refund-v4.pdf.

_________________

---

## Routing Decision #3

**Task đầu vào:**
> Ai phải phê duyệt để cấp quyền Level 3?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `policy keyword matched ('cấp quyền'). Choosed MCP search_kb. Didn't choose MCP get_ticket_info.`  
**MCP tools được gọi:** search_kb  
**Workers called sequence:** policy_tool_worker -> synthesis_worker

**Kết quả thực tế:**
- final_answer (ngắn): Yêu cầu được phê duyệt bởi Line Manager, IT Admin và IT Security.
- confidence:  1.0
- Correct routing? Yes

**Nhận xét:**
- Tương tự như câu trên, từ khóa "cấp quyền" đã kích hoạt đúng luồng kiểm tra chính sách. Worker đã truy xuất thành công file it/access-control-sop.md để trả lời chính xác các cấp phê duyệt cần thiết cho Level 3.
_________________

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> ERR-403-AUTH là lỗi gì và cách xử lý?

**Worker được chọn:** `human_review (sau đó chuyển sang retrieval_worker)`  
**Route reason:** `unknown error code + risk_high → human review. | human approved → retrieval`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**
- Cơ chế bảo vệ (Guardrail): Hệ thống nhận diện đây là mã lỗi lạ (unknown error code) và được gắn nhãn rủi ro cao (risk_high). Thay vì tự ý trả lời hoặc truy xuất ngay, Supervisor đã kích hoạt cơ chế Human-in-the-loop (HITL) để chờ con người phê duyệt luồng xử lý.

- Xử lý khi thiếu dữ liệu: Sau khi được con người phê duyệt để tìm kiếm, retrieval_worker đã cố gắng lục soát tài liệu nhưng không tìm thấy định nghĩa chính xác cho mã lỗi "ERR-403-AUTH".

_________________

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 7 | ~47% |
| policy_tool_worker | 7 | ~47~% |
| human_review | 1 | ~6% |

### Routing Accuracy

> Trong số X câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: 15 / 15
- Câu route sai (đã sửa bằng cách nào?): 0
- Câu trigger HITL: 1 (ERR-403-AUTH)

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. Keyword matching + policy keyword hoạt động rất hiệu quả khi kết hợp với risk_high flag.
2. Supervisor có khả năng gọi nhiều MCP tools cùng lúc (search_kb + get_ticket_info) khi task phức tạp → rất mạnh.
3. Default route dùng khi không match keyword rõ ràng vẫn fallback tốt vào retrieval.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?  
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

- Các route_reason trong trace rất rõ ràng, có chứa keyword cụ thể (“p1”, “hoàn tiền”, “cấp quyền”) và cả lý do chọn MCP tool. Đủ để debug dễ dàng. Không cần cải tiến lớn.

_________________
