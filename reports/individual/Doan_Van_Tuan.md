# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Đoàn Văn Tuấn
**Vai trò trong nhóm:** Worker Owner
**Ngày nộp:** 15/04/2026  

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
- File chính: `retrieval.py`, `synthesis.py`
- Functions tôi implement: `_get_embedding_fn`, `retrieve_sparse`, `retrieve_hybrid`, `_call_llm`, `_estimate_confidence`

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Trước tiên, tôi sử dụng LLM để tóm tắt lại kiến trúc cùng với những công việc cần làm để tất cả các thành viên có thể hiểu được luồng hoạt động của mình. Khi các công việc ở của các thành viên liên quan đế nhau thì tôi sẽ trao đổi với các thành viên để đảm bảo công việc của tôi được kết nối với công việc của các thành viên khác, cụ thể như của Khải làm graph có cần implement retrieval worker thì Khải sẽ note lại, để sau khi tôi triển khai xong phần lõi retrieval thì sẽ quay sang triển khai phần graph cho Khải.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Bằng chứng commit: 
eb5ced29bed2a5971995b55e5f1fdfee8708bfbd
ba475aad64ee4ae5de1938d83c9b8e99e5cd1c7c
818865a8b9d04dfe23e3f966b9d8adca26409cad
074ff1efdf224b4d0ae93aeb37524fb8f57f87d6
b38e32ac260c010bcce8069eb87d5ebb7b446a6e
...
---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Trong project thì tôi chủ động thử nghiệm cả 3 phương pháp retrieval là sparse, dense và hybrid để xem phương pháp nào phù hợp với dữ liệu của project. Sau khi thử nghiệm thì tôi thấy hybrid là phương pháp phù hợp nhất với dữ liệu của project. Những thử nghiệm này được thực hiện trên file `retrieval.py`.

**Lý do:**
Phương pháp Dense retrieval (vector/embedding) vượt trội trong việc hiểu ngữ nghĩa của câu hỏi (paraphrase) nhưng lại thường "trượt" các mã nội bộ cụ thể, rập khuôn như "P1", "ERR-403", "Level 3" vì vector dễ bị loãng. Trong khi đó Sparse retrieval (BM25) bắt keyword exact match cực kỳ tốt cho những ID đặc thù. Việc kết hợp 2 cách bằng Reciprocal Rank Fusion (RRF) ở `retrieve_hybrid` giúp cover chọn vẹn cả 2 điểm mạnh: không trật ngữ nghĩa và không làm mất mã lỗi kỹ thuật nhạy cảm.

**Trade-off đã chấp nhận:**
Gia tăng gấp đôi thời gian độ trễ nội bộ (latency) tại Node Retrieval bởi vì hệ thống phải chạy nạp index và truy vấn cho cả 2 pipeline (Dense lẫn BM25) thay vì một cái. Thêm vào đó, việc tính lại trọng số (RRF score calculation) cũng nới rộng thêm thời gian RAM xử lý so với Dense truyền thống.

**Bằng chứng từ trace/code:**

```python
    dense_results = retrieve_dense(query, top_k=top_k)
    sparse_results = retrieve_sparse(query, top_k=top_k)
    for text in all_texts:
        d_rank = dense_rank.get(text, len(dense_results))
        s_rank = sparse_rank.get(text, len(sparse_results))
        rrf_scores[text] = (
            dense_weight * (1 / (60 + d_rank)) + sparse_weight * (1 / (60 + s_rank))
        )
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Crash Pipeline do lỗi `NoneType is not iterable` và `KeyError: 'sources'` trong file phụ trách module `synthesis.py`.

**Symptom (pipeline làm gì sai?):**
Khi hệ thống chạy thử nghiệm một số query lỗi hoặc call AI API bị chập chờn, output báo lỗi exception thẳng lên terminal khiến Graph dừng khẩn cấp và in ra traceback, script bị ngắt, không thể trả về fallback default answer.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Lỗi nằm ngay tại logic của `synthesis_worker` (trong `_estimate_confidence` và hàm `run`). 
1. Ở `_estimate_confidence`, câu lệnh `if "Không đủ thông tin" in answer` mặc định xem `answer` luôn là chuỗi string. Nhưng khi `_call_llm` bị rớt mạng hoặc trả `None`, `answer` là `NoneType` sẽ ném văng Exception.
2. Dù nhảy xuống khối `except Exception as e:` của hàm `run()`, tôi lại quên gán mặc định cho thuộc tính `state["sources"] = []`, dẫn tới khi in kết quả `print(f"\nSources: {result['sources']}")` ở hàm main lại bị dính lỗi `KeyError`.

**Cách sửa:**
- Thêm cụm từ an toàn vào: `if answer is None or "Không đủ thông tin" in answer...` trong hàm đánh giá confidence.
- Trong block catch `except` của hàm `run`, bổ sung cứng dòng setup state khởi tạo: `state["sources"] = []` bảo đảm contract lúc nào cũng có đủ fields.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

*Trước khi sửa:*
```
Answer: SYNTHESIS_ERROR: argument of type 'NoneType' is not iterable
Traceback (most recent call last):
  File "workers/synthesis.py", line 224, in <module>
    print(f"\nSources: {result['sources']}")
KeyError: 'sources'
```

*Sau khi sửa:*
```
Answer: Khách hàng yêu cầu hoàn tiền cho đơn hàng Flash Sale ... [1]
Confidence: 0.83
synthesis_worker test done.
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã hoàn thiện suôn sẻ mô hình ghép nối Hybrid RRF cũng như cải tiến prompt mạnh mẽ để cài đặt tính năng `LLM-as-a-judge` định lượng tự động điểm số từ mức 1–5 cho confidence. Bắt nhịp luồng code tốt với các mô hình trước đó.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Đôi khi tôi mất cảnh giác với các tham số đầu vào bị lỗi ở các biên hệ thống (`None`, chuỗi rỗng) trong Python gây ra crash hệ thống ngoài mong đợi. Đáng lẽ các worker phải được bọc try/except bài bản hơn cho mọi key của Dictionary State.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
Synthesis và Retrieval là 2 node quyết định toàn khối tri thức của mạng RAG. Nếu tôi chưa cập nhật xong việc bóc tách Context và chuẩn hoá Output, thành viên phụ trách (như Khải đang vẽ Graph Agent) sẽ không có object input mô phỏng chuẩn nào để test sự liên thông nối nhau giữa các Nodes điều phối.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
Tôi phụ thuộc rành mạch vào cấu trúc đầu vào `AgentState` từ Graph Orchestrator (Khải) để biết chính xác Graph sẽ nhồi data format cho tool/context ra sao trước khi `synthesis` có thể xào nấu nên văn bản cuối.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ thử triển khai thêm cách sử dụng HyDE (Hypothetical Document Embeddings) để cải thiện khả năng truy xuất của Retriever. 

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
