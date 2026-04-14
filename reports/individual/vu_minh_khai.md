# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Vũ Minh Khải 
**Vai trò trong nhóm:** Supervisor Owner
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`
- Functions tôi implement: `supervisor_node (graph.py), analyze_policy (policy_tool.py)`

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Phần supervisor_node() đọc câu hỏi rồi quyết định gửi sang worker nào. Quyết định này ghi vào `supervisor_route`, `needs_tool`, `risk_high` — các bạn khác dựa vào đấy để biết có được gọi hay không, và có được dùng MCP tool không
_________________

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
Commit: eaa360b604e1bdd6ccf2fc0226421039d5d58e59 và cfaaf7fb5f6f458ecafcdc6405bb95ac33a25017
_________________

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** ___________________

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

_________________

**Trade-off đã chấp nhận:**

_________________

**Bằng chứng từ trace/code:**

```
[PASTE ĐOẠN CODE HOẶC TRACE RELEVANT VÀO ĐÂY]
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Thuộc tính run_id của class AgentState (graph.py) bị trùng giữa các lần run chạy sát nhau, dẫn đến file trace bị ghi đè.
_________________
**Symptom (pipeline làm gì sai?):**
Khi chạy nhiều query liên tiếp trong vòng lặp `test_queries` của `graph.py`, do tốc độ chạy khá nhanh, thư mục `./artifacts/traces/` chỉ còn **1 file JSON cuối cùng** thay vì 3 file tương ứng 3 query. Các trace trước bị mất, khiến việc debug routing và so sánh giữa các run không thực hiện được.
_________________

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Lỗi nằm ở tầng **contract/identity của state**, cụ thể là `make_initial_state()` trong `graph.py`. `run_id` ban đầu chỉ dùng `datetime.now().strftime('%Y%m%d_%H%M%S')` — độ phân giải chỉ tới giây. Khi pipeline chạy nhanh hơn 1 giây/run (các query ngắn, không gọi LLM), hai run liên tiếp sinh cùng một `run_id`. Hàm `save_trace()` dùng `run_id` làm tên file nên file sau ghi đè file trước.
_________________

**Cách sửa:**
Gắn thêm suffix ngẫu nhiên `uuid.uuid4().hex[:12]` vào `run_id` để đảm bảo tính duy nhất kể cả trong cùng 1 giây:
```python
"run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:12]}"
```

_________________

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.
- Cái này ko có bằng chứng cụ thể... Sau khi chạy 3 queries thì trong artifacts/traces chỉ còn duy nhất 1 file kết quả của query cuối cùng.
- Sau khi sửa, kết quả chạy của từng query được lưu ở 1 file riêng.
_________________

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

_________________

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

_________________

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

_________________

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

_________________

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
