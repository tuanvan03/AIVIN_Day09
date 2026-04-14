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

**Quyết định:** Trong `analyze_policy` (policy_tool.py), tôi giữ nguyên rule-based check để xác định `policy_applies` và `exceptions_found`, bổ sung thêm các keyword để xác định chính xác hơn, sử dụng regex để bắt ngày tháng...

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**
- Nhanh, chính xác.
- Không phụ thuộc vào API OpenAI bên ngoài (có thể bị lỗi...)
- Tránh được việc LLM bịa thêm thứ ngoài context.
- Không tốn chi phí cho LLM API
_________________

**Trade-off đã chấp nhận:**
- Phần `explanation` viết bằng rule-based nên hơi cứng, không tự nhiên như LLM diễn giải. User đọc sẽ thấy giống template hơn là câu trả lời "người" — chấp nhận được vì bên synthesis vẫn có LLM để viết `final_answer` mượt lại.
- Khó mở rộng khi policy thêm exception mới: phải tự tay thêm keyword list, không tự học được từ context như LLM.
- Với câu hỏi mơ hồ (không chứa keyword flash sale / license / activated), rule-based sẽ mặc định `policy_applies=True` — có thể bỏ sót exception lạ. Cái này để synthesis + human_review bắt sau.

_________________

**Bằng chứng từ trace/code:**
Phần sau thuộc hàm analyze_policy() file policy_tool.py
```
[PASTE ĐOẠN CODE HOẶC TRACE RELEVANT VÀO ĐÂY]
```
    # Exception 1: Flash Sale
    flash_kw = ("flash sale", "flash-sale", "flashsale", "sale chớp nhoáng", "giảm giá chớp nhoáng", "đợt sale", "sale sốc")
    if any(k in task_lower for k in flash_kw) or any(k in context_text for k in flash_kw):
        exceptions_found.append({
            "type": "flash_sale_exception",
            "rule": "Đơn hàng Flash Sale không được hoàn tiền (Điều 3, chính sách v4).",
            "source": "policy_refund_v4.txt",
        })

    # Exception 2: Digital product
    digital_kw = (
        "license key", "license", "subscription", "kỹ thuật số",
        "digital", "phần mềm", "software", "mã kích hoạt",
        "key bản quyền", "sản phẩm số"
    )
    if any(kw in task_lower for kw in digital_kw):
        exceptions_found.append({
            "type": "digital_product_exception",
            "rule": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền (Điều 3).",
            "source": "policy_refund_v4.txt",
        })

    # Exception 3: Activated product
    activated_kw = (
        "đã kích hoạt", "đã đăng ký", "đã sử dụng", "activated",
        "đã dùng", "đã mở", "đã khởi tạo", "đã nhập key",
        "đã redeem", "redeemed", "tài khoản đã tạo", "đã active"
    )
    if any(kw in task_lower for kw in activated_kw):
        exceptions_found.append({
            "type": "activated_exception",
            "rule": "Sản phẩm đã kích hoạt hoặc đăng ký tài khoản không được hoàn tiền (Điều 3).",
            "source": "policy_refund_v4.txt",
        })

    # Determine policy_applies
    policy_applies = len(exceptions_found) == 0

    # Determine which policy version applies (temporal scoping)
    # TODO: Check nếu đơn hàng trước 01/02/2026 → v3 applies (không có docs, nên flag cho synthesis)
    policy_name = "refund_policy_v4"
    policy_version_note = ""
    v3_phrases = (
        "31/01", "30/01", "29/01", "28/01",
        "trước 01/02", "trước 1/2", "trước 01/02/2026", "trước 1/2/2026",
        "tháng 1/2026", "tháng 01/2026", "january 2026",
        "policy v3", "chính sách v3", "chính sách cũ", "policy cũ"
    )
    if any(p in task_lower for p in v3_phrases):
        policy_version_note = "Đơn hàng đặt trước 01/02/2026 áp dụng chính sách v3 (không có trong tài liệu hiện tại)."
    
    if not policy_version_note:
        m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", task)
        if m:
            try:
                d, mo, y = map(int, m.groups())
                order_date = datetime(y, mo, d)
                if order_date < datetime(2026, 2, 1):
                    policy_version_note = (
                        f"Đơn ngày {order_date.strftime('%d/%m/%Y')} áp dụng chính sách v3 "
                        f"(không có trong tài liệu hiện tại)."
                    )
            except ValueError:
                pass
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
- Bổ sung và chỉnh sửa các điểm yếu cho rule-based.
- Quyết định tắt LLM ở analyze_policy() sau khi thấy phần đó ko cần thiết, tiết kiệm chi phí...
_________________

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Supervisor routing của tôi còn nặng keyword — những câu hỏi không chứa từ khoá trong list sẽ rơi mặc định về `retrieval_worker`, không có fallback thông minh. Phần `explanation` rule-based viết cứng, chưa tự nhiên.
_________________

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
- `supervisor_node` là cổng vào graph — nếu tôi route sai thì cả pipeline (retrieval, synthesis) chạy sai theo.
- `analyze_policy` quyết định `policy_applies` và `exceptions_found` — synthesis phụ thuộc cái này để viết câu trả lời cuối, nếu tôi bỏ sót exception thì user nhận câu sai.

_________________

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
- Cần `retrieval_worker` trả `retrieved_chunks` đúng format (`text`, `source`) để `analyze_policy` đọc context.
- Cần `mcp_server.dispatch_tool` hoạt động ổn để `_call_mcp_tool` trong policy_tool.py không fail.

_________________

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*1 

_________________
> Tôi sẽ thử nghiệm dùng một mô hình LLM nhỏ để routing ở supervisor_node(). Hiện tại đang dùng rule_based. Lý do trước đó cài đặt rule_based, một phần là do bài tập yêu cầu, một phần là cần phải làm gấp để làm phần khác, và để các thành viên khác ko bị ảnh hưởng. Sử dụng LLM nhỏ sẽ tốn thêm chi phí nhưng cũng có thể tăng độ chính xác. Tôi sẽ xây dựng 1 bộ dữ liệu đánh giá khoảng 20 câu để đánh giá nhanh xem cách nào tốt hơn.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
