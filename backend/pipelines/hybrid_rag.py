import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vector_store import search, get_all
from llm_handler import generate_response
from reranker import rerank
from rank_bm25 import BM25Okapi
from typing import Dict, List
import time


# ── Helper: Get All Chunks (for BM25) ──────────────────────────
# BM25 is an in-memory keyword search algorithm.
# It needs ALL document chunks loaded at once to build its index.
# So we fetch every chunk stored in FAISS for this document.
def get_all_chunks(doc_id: str) -> List[Dict]:
    all_chunks = get_all(doc_id, "chunks")
    return all_chunks


# ── Helper: BM25 Keyword Search ───────────────────────────────────────────────
# BM25 (Best Match 25) is a classic keyword-based ranking algorithm.
# It finds chunks that contain the exact words from the query.
# Unlike vector search, it doesn't understand meaning — it matches words.
#
# Steps:
#   1. Tokenize (split into words) all chunks → build BM25 index
#   2. Tokenize the query
#   3. Score every chunk against the query
#   4. Return top_k highest scoring chunks
def bm25_search(query: str, all_chunks: List[Dict], top_k: int = 5) -> List[Dict]:

    if not all_chunks:
        return []

    # Step 1: Tokenize all chunk texts (lowercase + split by spaces)
    # BM25 works on word tokens, not full sentences
    tokenized_corpus = [chunk["content"].lower().split() for chunk in all_chunks]

    # Step 2: Build BM25 index from all tokenized chunks
    bm25 = BM25Okapi(tokenized_corpus)

    # Step 3: Tokenize the query the same way
    tokenized_query = query.lower().split()

    # Step 4: Get BM25 scores for ALL chunks
    # scores[i] = how relevant all_chunks[i] is to the query
    scores = bm25.get_scores(tokenized_query)

    # Step 5: Get top_k indices with highest scores
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    # Step 6: Build result list with the top chunks + their BM25 scores
    results = []
    for idx in top_indices:
        if scores[idx] > 0:    # only include chunks with a positive score
            chunk = all_chunks[idx].copy()
            chunk["bm25_score"] = round(float(scores[idx]), 4)
            results.append(chunk)

    return results


# ── Function: Generate Query Variations (Multi-Query) ────────────────────────
# Same as Pipeline 2 — ask LLM to generate 3 versions of the question
def generate_query_variations(question: str) -> List[str]:

    prompt = f"""Generate exactly 3 different versions of the following question.
Each version should ask for the same information but use different wording.
Return ONLY the 3 questions, one per line. No numbering, no extra text.

Original question: {question}

3 variations:"""

    result = generate_response(prompt)
    raw_text = result["answer"]

    variations = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
    all_queries = [question] + variations[:3]

    return all_queries


# ── Function: Build Prompt ────────────────────────────────────────────────────
def build_prompt(question: str, chunks: List[Dict]) -> str:

    context = "\n\n---\n\n".join([chunk["content"] for chunk in chunks])

    prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided document context.

IMPORTANT RULES:
- Answer ONLY using the information found in the context below.
- If the answer is not present in the context, say: "I could not find this information in the uploaded document."
- Do not use any outside knowledge.
- Be clear and concise.

CONTEXT FROM DOCUMENT:
{context}

QUESTION:
{question}

ANSWER:"""

    return prompt


# ── Main Function: Run Hybrid RAG + Multi-Query Pipeline ─────────────────────
# Full pipeline:
#   Step 1 → Generate 3-4 query variations (Multi-Query)
#   Step 2 → For each variation:
#              a) Vector search  (semantic meaning)
#              b) BM25 search    (keyword matching)
#   Step 3 → Merge ALL results and deduplicate
#   Step 4 → Re-rank merged results
#   Step 5 → Build prompt → LLM → Return answer
def run(doc_id: str, question: str, top_k: int = 5) -> Dict:

    start_time = time.time()

    # ── Step 1: Generate query variations ────────────────────────────────────
    all_queries = generate_query_variations(question)
    print(f"[Pipeline3] Generated {len(all_queries)} queries: {all_queries}")

    # ── Step 2a: Load ALL chunks once (needed for BM25) ──────────────────────
    all_chunks = get_all_chunks(doc_id)

    # ── Step 2b: Run Vector + BM25 search for each query variation ───────────
    all_results = []

    for query in all_queries:

        # Vector search → semantic matches (from ChromaDB)
        vector_results = search(
            doc_id=doc_id,
            query=query,
            collection_type="chunks",
            top_k=top_k
        )

        # BM25 search → keyword matches (from in-memory index)
        bm25_results = bm25_search(
            query=query,
            all_chunks=all_chunks,
            top_k=top_k
        )

        all_results.extend(vector_results)
        all_results.extend(bm25_results)

    # ── Step 3: Deduplicate ───────────────────────────────────────────────────
    seen_contents = set()
    unique_results = []
    for result in all_results:
        if result["content"] not in seen_contents:
            seen_contents.add(result["content"])
            unique_results.append(result)

    print(f"[Pipeline3] {len(all_results)} total results -> {len(unique_results)} unique after dedup")

    if not unique_results:
        return {
            "pipeline": "hybrid_rag",
            "answer": "No relevant content found in the document for your question.",
            "model_used": "none",
            "retrieved_chunks": [],
            "response_time_seconds": 0
        }

    # ── Step 4: Re-rank ───────────────────────────────────────────────────────
    reranked_chunks = rerank(question=question, chunks=unique_results, top_k=3)

    # ── Step 5: Build prompt → LLM ───────────────────────────────────────────
    prompt = build_prompt(question, reranked_chunks)
    llm_result = generate_response(prompt)

    end_time = time.time()
    response_time = round(end_time - start_time, 2)

    return {
        "pipeline": "hybrid_rag",
        "answer": llm_result["answer"],
        "model_used": llm_result["model_used"],
        "queries_used": all_queries,
        "retrieved_chunks": reranked_chunks,
        "response_time_seconds": response_time
    }
