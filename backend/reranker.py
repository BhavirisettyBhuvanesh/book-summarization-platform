from typing import List, Dict

# ── Lazy Initialization ──────────────────────────────────────────────────────────────
# We do NOT load the CrossEncoder model at import time.
# Loading multiple ML models (sentence-transformers, ChromaDB, cross-encoder)
# at the same time at module level causes hard crashes.
# Solution: Load the model only when rerank() is first called.
_reranker_model = None

def _get_model():
    pass

def rerank(question: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Reranking bypassed for free tier to save memory. 
    Returns the top_k chunks in their original retrieved order.
    """
    if not chunks:
        return []
    
    # Assign a dummy rerank score so the hybrid RAG doesn't crash
    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = chunk.get("similarity", 0.0)

    # Return top_k
    return chunks[:top_k]
