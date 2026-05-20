from typing import List, Dict

# ── Lazy Initialization ──────────────────────────────────────────────────────────────
# We do NOT load the CrossEncoder model at import time.
# Loading multiple ML models (sentence-transformers, ChromaDB, cross-encoder)
# at the same time at module level causes hard crashes.
# Solution: Load the model only when rerank() is first called.
_reranker_model = None

def _get_model():
    global _reranker_model
    if _reranker_model is None:
        from sentence_transformers import CrossEncoder
        _reranker_model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            device="cpu"
        )
    return _reranker_model


# ── Main Function: Rerank Chunks ──────────────────────────────────────────────
# Takes the question and a list of retrieved chunks.
# Scores each chunk against the question.
# Returns the top_k chunks sorted by relevance score (best first).
#
# question   = the user's original question
# chunks     = list of chunk dicts retrieved from vector_store.search()
# top_k      = how many top chunks to keep after re-ranking (default: 3)
def rerank(question: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:

    if not chunks:
        return []

    model = _get_model()   # load model on first use

    pairs = [[question, chunk["content"]] for chunk in chunks]
    scores = model.predict(pairs)

    # Step 3: Attach the rerank score to each chunk dict
    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = round(float(scores[i]), 4)

    # Step 4: Sort chunks by rerank_score — highest score first
    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

    # Step 5: Keep only the top_k most relevant chunks
    return reranked[:top_k]
