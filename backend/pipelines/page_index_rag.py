import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vector_store import search
from llm_handler import generate_response
from reranker import rerank
from typing import Dict, List
import time


# ── Function 1: Generate Query Variations ────────────────────────────────────
# This is the MULTI-QUERY part of this pipeline.
# We send the user's original question to the LLM and ask it to
# generate 3 different versions of the same question.
#
# Why? Different phrasings retrieve different pages from ChromaDB,
# giving us much better coverage of the document.
#
# Example:
#   Original:   "What are the causes of climate change?"
#   Variation 1: "What factors contribute to climate change?"
#   Variation 2: "Why is global warming happening?"
#   Variation 3: "What leads to rising global temperatures?"
def generate_query_variations(question: str) -> List[str]:

    prompt = f"""Generate exactly 3 different versions of the following question.
Each version should ask for the same information but use different wording.
Return ONLY the 3 questions, one per line. No numbering, no extra text.

Original question: {question}

3 variations:"""

    result = generate_response(prompt)
    raw_text = result["answer"]

    # Split the response by newlines to get individual questions
    # Filter out any empty lines
    variations = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]

    # Always include the original question too
    all_queries = [question] + variations[:3]   # original + max 3 variations = 4 total

    return all_queries


# ── Function 2: Build the Prompt ─────────────────────────────────────────────
# Same guardrail as Pipeline 1 — only answer from document context.
# The difference is our context now comes from full pages (not small chunks).
def build_prompt(question: str, pages: List[Dict]) -> str:

    context = "\n\n---\n\n".join([
        f"[Page {p['metadata'].get('page_number', '?')}]\n{p['content']}"
        for p in pages
    ])

    prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided document context.

IMPORTANT RULES:
- Answer ONLY using the information found in the context below.
- If the answer is not present in the context, say: "I could not find this information in the uploaded document."
- Do not use any outside knowledge.
- Be clear and concise.
- If relevant, mention which page the information came from.

CONTEXT FROM DOCUMENT:
{context}

QUESTION:
{question}

ANSWER:"""

    return prompt


# ── Main Function: Run Page Indexing RAG + Multi-Query Pipeline ───────────────
# Full pipeline:
#   Step 1 → Generate 3-4 query variations using LLM (Multi-Query)
#   Step 2 → Search ChromaDB PAGES collection for each variation
#   Step 3 → Merge all results and remove duplicate pages
#   Step 4 → Re-rank the merged pages using cross-encoder
#   Step 5 → Build prompt with top re-ranked pages
#   Step 6 → Send to LLM → return answer
def run(doc_id: str, question: str, top_k: int = 5) -> Dict:

    start_time = time.time()

    # ── Step 1: Generate query variations ────────────────────────────────────
    all_queries = generate_query_variations(question)
    print(f"[Pipeline2] Generated {len(all_queries)} queries: {all_queries}")

    # ── Step 2: Search pages collection for each query variation ──────────────
    all_results = []
    for query in all_queries:
        results = search(
            doc_id=doc_id,
            query=query,
            collection_type="pages",   # ← uses PAGE-level index (not chunks)
            top_k=top_k
        )
        all_results.extend(results)

    # ── Step 3: Deduplicate — remove pages that were returned multiple times ──
    # We use the page content as the key to detect duplicates
    seen_contents = set()
    unique_results = []
    for result in all_results:
        if result["content"] not in seen_contents:
            seen_contents.add(result["content"])
            unique_results.append(result)

    print(f"[Pipeline2] Retrieved {len(all_results)} total -> {len(unique_results)} unique pages after dedup")

    if not unique_results:
        return {
            "pipeline": "page_index_rag",
            "answer": "No relevant content found in the document for your question.",
            "model_used": "none",
            "retrieved_pages": [],
            "response_time_seconds": 0
        }

    # ── Step 4: Re-rank all unique pages ─────────────────────────────────────
    # Cross-encoder reads [question + page] and gives relevance score
    # We keep top 3 most relevant pages
    reranked_pages = rerank(question=question, chunks=unique_results, top_k=3)

    # ── Step 5: Build prompt with top re-ranked pages ─────────────────────────
    prompt = build_prompt(question, reranked_pages)

    # ── Step 6: Send to LLM and get answer ───────────────────────────────────
    llm_result = generate_response(prompt)

    end_time = time.time()
    response_time = round(end_time - start_time, 2)

    return {
        "pipeline": "page_index_rag",
        "answer": llm_result["answer"],
        "model_used": llm_result["model_used"],
        "queries_used": all_queries,            # all query variations used
        "retrieved_pages": reranked_pages,      # pages used to answer
        "response_time_seconds": response_time
    }
