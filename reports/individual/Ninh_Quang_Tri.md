# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Ninh Quang Trí
**Vai trò trong nhóm:** MCP Owner / Trace Owner  
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

> Tôi phụ trách phần Sprint 3 MCP và một phần của Sprint 4 tôi chạy và nhập các kết quả từ lab 4 và viết các delta so sánh ở trong file `eval_trace.py`ở function `compare_single_vs_multi`. 
> Trong MCP, tôi thay đổi retrieval dense từ code gốc sang retrieval hybrid mà nhóm tôi đã chọn, những thay đổi được thực hiện trong file `mcp_server.py` ở function `tool_search_kb`, thay đổi `retrieve_dense` thành `retrieve_hybrid`.
> Tôi thay đổi `policy_tool.py` ở function `run` để `state["route_reason"]` có thể ghi xem MCP có được sử dụng hay không

**Module/file tôi chịu trách nhiệm:**
- File chính: `mcp_server.py`, `policy_tool.py`và `eval_trace.py`
- Functions tôi implement: `tool_search_kb`, `run` và `compare_single_vs_multi`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

`retrieve_hybrid` của Tuấn được dùng trong `tool_search_kb` của tôi. Tôi hoàn thành các thay đổi trong `policy_tool.py` của Khải để `state["route_reason"]` có thể ghi xem MCP có được sử dụng hay không. `eval_trace.py` của tôi dùng `compare_single_vs_multi` để so sánh kết quả của MCP và single-agent giúp Bình làm document.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

`de4b599ddc8189b133757c3366fc9ad5f7f98004`, `db32b05789494b9c06b128a59763f81222bf6a23`, `dd79b6eeb257d1b25976e3f4e61ca6d069a76c30`

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Tôi đã thêm vào `state["route_reason"]` để ghi xem MCP có được sử dụng hay không.
> Các lựa chọn thay thế là trong `state["route_reason"]` ghi xem MCP có được sử dụng nhưng không ghi MCP không được sử dụng.
> Tôi chọn cách này vì nó giúp tôi dễ dàng kiểm tra xem MCP có được sử dụng hay không.
> Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Tôi đã thêm vào `state["route_reason"]` để ghi xem MCP có được sử dụng hay không.

**Lý do:**

Tôi chọn cách này vì nó giúp tôi dễ dàng kiểm tra xem MCP có được sử dụng hay không.

**Trade-off đã chấp nhận:**

Tôi đã từ bỏ implement MCP bằng HTTP server và dùng function call để MCP có thể chạy được.

**Bằng chứng từ trace/code:**

```
    state["route_reason"] = state["route_reason"] + "Choosed MCP get_ticket_info. "
else:
    state["route_reason"] = state["route_reason"] + "Didn't choose MCP get_ticket_info."
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Bug MCP không được sử dụng, cũng không log việc MCP không được sử dụng

**Symptom (pipeline làm gì sai?):**

Khi chạy `eval_trace.py` file `eval_report.json`, trong key `route_reason:` không có nói liệu MCP có được dùng hay không và `"mcp_usage_rate":` luôn là 0/15.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Trong `policy_tool.py` function `run` không có ghi vào `state["route_reason"]` liệu MCP có được sử dụng hay không.
Đồng thời phần import worker trong `graph.py` cũng chưa call các function trong folder `workers`

**Cách sửa:**

Thêm `from workers.retrieval import run as retrieval_run from workers.policy_tool import run as policy_tool_run from workers.synthesis import run as synthesis_run` vào `graph.py` và thêm `state["route_reason"] = state["route_reason"] + "Choosed MCP get_ticket_info. "` vào `policy_tool.py` function `run`.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

Trước:
```
"route_reason": "policy keyword matched ('access').  | risk_high flagged."
"avg_confidence": 0.917,
    "avg_latency_ms": 5015,
    "mcp_usage_rate": "0/15 (0%)",
    "hitl_rate": "0/15 (0%)",
```

Sau:
```
"route_reason": "policy keyword matched ('access').  | risk_high flagged. Choosed MCP search_kb. Choosed MCP get_ticket_info. "
"avg_confidence": 0.917,
    "avg_latency_ms": 5015,
    "mcp_usage_rate": "7/15 (46%)",
    "hitl_rate": "1/15 (6%)",
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)


**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt nhất ở việc sửa lỗi MCP không được sử dụng, cũng không log việc MCP không được sử dụng. Tôi đã sửa lỗi này trong `policy_tool.py` function `run` và thêm `state["route_reason"] = state["route_reason"] + "Choosed MCP get_ticket_info. "` vào `policy_tool.py` function `run`.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi làm chưa tốt ở việc chưa pull code của Tuấn ở đoạn `from workers.retrieval import run as retrieval_run from workers.policy_tool import run as policy_tool_run from workers.synthesis import run as synthesis_run` để MCP có thể chạy được.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nhóm phụ thuộc vào tôi ở phần `eval_trace.py` function `compare_single_vs_multi` để so sánh kết quả của MCP và single-agent giúp Bình làm document và `mcp_server.py` function `tool_search_kb` để thay đổi `retrieve_dense` thành `retrieve_hybrid`.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào Tuấn ở phần `mcp_server.py` function `tool_search_kb` để thay đổi `retrieve_dense` thành `retrieve_hybrid` và Khải ở phần `policy_tool.py` function `run` để ghi vào `state["route_reason"]` liệu MCP có được sử dụng hay không.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

_________________

Tôi sẽ thử implement MCP server thật dùng mcp library hoặc HTTP server.

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
