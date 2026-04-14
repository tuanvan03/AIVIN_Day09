# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Nhóm-03-E402   
**Ngày:** 14/04/2026

> **Hướng dẫn:** So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker).
> Phải có **số liệu thực tế** từ trace — không ghi ước đoán.
> Chạy cùng test questions cho cả hai nếu có thể.

---

## 1. Metrics Comparison

> Điền vào bảng sau. Lấy số liệu từ:
> - Day 08: chạy `python eval.py` từ Day 08 lab
> - Day 09: chạy `python eval_trace.py` từ lab này

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.83 | 0.917 | +0.087 | Tăng rõ rệt |
| Avg latency (ms) | 2547.71 | 5015 | +2467.29 | Gấp ~2 lần |
| Abstain rate (%) | 33% | 6.67% | -26.33% | Giảm mạnh |
| Multi-hop accuracy | 72% | 93% | +21% | % câu multi-hop trả lời đúng |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | |
| Debug time (estimate) | 12-15 phút | 3-5 phút | -9 phút | Thời gian tìm ra 1 bug |
| HITL trigger rate | N/A | 6.67% | N/A | An toàn hơn |

> **Lưu ý:** Nếu không có Day 08 kết quả thực tế, ghi "N/A" và giải thích.

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | ~85%~ | 100% |
| Latency | ~2200ms | ~3100ms |
| Observation | Thường retrieve đúng nhưng đôi khi hallucinate nhẹ | Luôn retrieve đúng tài liệu, synthesis ổn định |

**Kết luận:** Multi-agent có cải thiện không? Tại sao có/không?
- Multi-agent cải thiện rõ ở accuracy và consistency vì có worker chuyên trách retrieval và synthesis riêng biệt.

_________________

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | 72% | ~93% |
| Routing visible? | ✗ | ✓ |
| Observation | Thường lẫn lộn thông tin hoặc miss 1 nguồn | Supervisor route đúng policy/SLA → lấy đủ sources |

**Kết luận:**
- Đây là điểm cải thiện mạnh nhất của multi-agent. Khả năng route chính xác + gọi nhiều MCP tool giúp xử lý tốt các câu phức tạp.
_________________

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | 33% | 6.67% |
| Hallucination cases | 3-4 cases | 0 cases |
| Observation | Hay cố trả lời khi không có data | Trigger human_review khi risk_high hoặc unknown error |

**Kết luận:**
- Multi-agent an toàn hơn nhiều, giảm hallucination đáng kể nhờ risk detection và HITL.

_________________

---

## 3. Debuggability Analysis

> Khi pipeline trả lời sai, mất bao lâu để tìm ra nguyên nhân?

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: 12-15 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: ___ phút
```3-5

**Câu cụ thể nhóm đã debug:** 

- Câu ERR-403-AUTH — ban đầu route sai sang retrieval. Trace cho thấy risk_high + unknown error code → supervisor route sang human_review đúng. Dễ dàng xác định và confirm chỉ trong 2 phút.

_________________

---

## 4. Extensibility Analysis

> Dễ extend thêm capability không?

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

**Nhận xét:**
- Multi-agent dễ mở rộng hơn rất nhiều.

_________________

---

## 5. Cost & Latency Trade-off

> Multi-agent thường tốn nhiều LLM calls hơn. Nhóm đo được gì?

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 2 LLM calls |
| Complex query | 1 LLM call | 3-4 LLM calls |
| MCP tool call | N/A | 1-2 |

**Nhận xét về cost-benefit:**

- Latency tăng gấp đôi nhưng đổi lại accuracy cao hơn, debug dễ hơn, extensibility tốt hơn và an toàn hơn (ít hallucination). Trong production, tradeoff này hoàn toàn đáng giá.

_________________

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**

1. Routing intelligence + visibility (route_reason) giúp hệ thống quyết định đúng worker.
2. Modularity: Mỗi worker có thể phát triển/test độc lập.
3. Safety: Risk detection + HITL + policy tool giảm hallucination mạnh.
4. Extensibility: Dễ thêm tool/domain mới mà không phá vỡ core.


> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Latency cao hơn (gần gấp đôi).
2. Phức tạp hơn khi implement ban đầu.

> **Khi nào KHÔNG nên dùng multi-agent?**

1. Ứng dụng rất đơn giản, ít domain, latency cực kỳ quan trọng (dưới 1 giây).
2. Team nhỏ, không có nhu cầu maintain lâu dài.

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

1. Evaluation framework tự động so sánh output của các worker.
2. Memory giữa các worker (shared state).
