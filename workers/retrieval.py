"""
workers/retrieval.py — Retrieval Worker
Sprint 2: Implement retrieval từ ChromaDB, trả về chunks + sources.

Input (từ AgentState):
    - task: câu hỏi cần retrieve
    - (optional) retrieved_chunks nếu đã có từ trước

Output (vào AgentState):
    - retrieved_chunks: list of {"text", "source", "score", "metadata"}
    - retrieved_sources: list of source filenames
    - worker_io_log: log input/output của worker này

Gọi độc lập để test:
    python workers/retrieval.py
"""

"""
!pip install rank-bm25 underthesea
"""

import os
import sys

# ─────────────────────────────────────────────
# Worker Contract (xem contracts/worker_contracts.yaml)
# Input:  {"task": str, "top_k": int = 3}
# Output: {"retrieved_chunks": list, "retrieved_sources": list, "error": dict | None}
# ─────────────────────────────────────────────

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3

from dotenv import load_dotenv
load_dotenv()

def _get_embedding_fn():
    """
    Trả về embedding function.
    TODO Sprint 1: Implement dùng OpenAI hoặc Sentence Transformers.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        def embed(text: str) -> list:
            resp = client.embeddings.create(input=text, model="text-embedding-3-small")
            return resp.data[0].embedding
        return embed
    except ImportError:
        pass

def _get_collection():
    """
    Kết nối ChromaDB collection.
    TODO Sprint 2: Đảm bảo collection đã được build từ Step 3 trong README.
    """
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = client.get_collection("rag_lab")
    except Exception:
        # Auto-create nếu chưa có
        collection = client.get_or_create_collection(
            "rag_lab",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"⚠️  Collection 'rag_lab' chưa có data. Chạy index script trong README trước.")
    return collection


def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    """
    Dense retrieval: embed query → query ChromaDB → trả về top_k chunks.

    TODO Sprint 2: Implement phần này.
    - Dùng _get_embedding_fn() để embed query
    - Query collection với n_results=top_k
    - Format result thành list of dict

    Returns:
        list of {"text": str, "source": str, "score": float, "metadata": dict}
    """
    # TODO: Implement dense retrieval
    embed = _get_embedding_fn()
    query_embedding = embed(query)

    try:
        collection = _get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        chunks = []
        for i, (doc, dist, meta) in enumerate(zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0]
        )):
            chunks.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "score": round(1 - dist, 4),  # cosine similarity
                "metadata": meta,
            })
        return chunks

    except Exception as e:
        print(f"⚠️  ChromaDB query failed: {e}")
        # Fallback: return empty (abstain)
        return []


def retrieve_sparse(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    """
    Sparse retrieval: tìm kiếm theo keyword (BM25).

    Mạnh ở: exact term, mã lỗi, tên riêng (ví dụ: "ERR-403", "P1", "refund")
    Hay hụt: câu hỏi paraphrase, đồng nghĩa
    """
    try:
        from underthesea import word_tokenize
        from rank_bm25 import BM25Okapi
    except ImportError:
        print("⚠️  Thiếu thư viện underthesea hoặc rank-bm25. Vui lòng cài đặt: pip install underthesea rank-bm25")
        return []

    collection = _get_collection()
    all_data = collection.get(include=["documents", "metadatas"])
    
    if not all_data or not all_data.get("documents"):
        return []

    all_chunks = [
        {"text": doc, "metadata": meta}
        for doc, meta in zip(all_data["documents"], all_data["metadatas"])
    ]

    corpus = [chunk["text"] for chunk in all_chunks]
    tokenized_corpus = [word_tokenize(doc.lower(), format="list") for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = word_tokenize(query.lower(), format="list")
    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    return [
        {
            "text": all_chunks[i]["text"],
            "source": all_chunks[i]["metadata"].get("source", "unknown"),
            "metadata": all_chunks[i]["metadata"],
            "score": float(scores[i])
        }
        for i in top_indices
    ]


def retrieve_hybrid(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
) -> list:
    """
    Hybrid retrieval: kết hợp dense và sparse bằng Reciprocal Rank Fusion (RRF).

    Mạnh ở: giữ được cả nghĩa (dense) lẫn keyword chính xác (sparse)
    Phù hợp khi: corpus lẫn lộn ngôn ngữ tự nhiên và tên riêng/mã lỗi/điều khoản
    """
    dense_results = retrieve_dense(query, top_k=top_k)
    sparse_results = retrieve_sparse(query, top_k=top_k)

    # Gán rank cho từng doc theo text (dùng text làm key)
    dense_rank = {c["text"]: i for i, c in enumerate(dense_results)}
    sparse_rank = {c["text"]: i for i, c in enumerate(sparse_results)}

    # Gom tất cả unique docs
    all_texts = {c["text"]: c for c in dense_results + sparse_results}

    # Tính RRF score cho từng doc
    rrf_scores = {}
    for text in all_texts:
        d_rank = dense_rank.get(text, len(dense_results))
        s_rank = sparse_rank.get(text, len(sparse_results))
        rrf_scores[text] = (
            dense_weight * (1 / (60 + d_rank)) +
            sparse_weight * (1 / (60 + s_rank))
        )

    # Sort theo RRF score giảm dần, trả về top_k
    sorted_texts = sorted(rrf_scores, key=lambda t: rrf_scores[t], reverse=True)[:top_k]
    return [
        {**all_texts[t], "score": rrf_scores[t]}
        for t in sorted_texts
    ]


def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với retrieved_chunks và retrieved_sources
    """
    task = state.get("task", "")
    top_k = state.get("retrieval_top_k", DEFAULT_TOP_K)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])

    state["workers_called"].append(WORKER_NAME)

    # Log worker IO (theo contract)
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }

    try:
        chunks = retrieve_hybrid(task, top_k=top_k)

        sources = list({c["source"] for c in chunks})

        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks),
            "sources": sources,
        }
        state["history"].append(
            f"[{WORKER_NAME}] retrieved {len(chunks)} chunks from {sources}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    # Ghi worker IO vào state để trace
    state.setdefault("worker_io_logs", []).append(worker_io)

    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        
        # print("\n  --- Dense Retrieval ---")
        # chunks_dense = retrieve_dense(query)
        # print(f"  Retrieved: {len(chunks_dense)} chunks")
        # for c in chunks_dense[:2]:
        #     print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")

        # print("\n  --- Sparse Retrieval ---")
        # chunks_sparse = retrieve_sparse(query)
        # print(f"  Retrieved: {len(chunks_sparse)} chunks")
        # for c in chunks_sparse[:2]:
        #     print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")

        # print("\n  --- Hybrid Retrieval ---")
        # chunks_hybrid = retrieve_hybrid(query)
        # print(f"  Retrieved: {len(chunks_hybrid)} chunks")
        # for c in chunks_hybrid[:2]:
        #     print(f"    [{c['score']:.3f}] {c['source']}: {c['text']}")
        result = run({"task": query})
        chunks = result.get("retrieved_chunks", [])
        print(f"  Retrieved: {len(chunks)} chunks")
        for c in chunks[:2]:
            print(f"    [{c['score']:.3f}] {c['source']}: {c['text']}")
        print(f"  Sources: {result.get('retrieved_sources', [])}")

    print("\n✅ retrieval_worker test done.")
