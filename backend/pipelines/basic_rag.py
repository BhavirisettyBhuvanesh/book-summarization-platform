import sys
import os

# Add the backend folder to path so we can import our other files
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vector_store import search
from llm_handler import generate_response
from typing import Dict
import time


# ── Helper: Build the Prompt ──────────────────────────────────────────────────
# This function takes the user's question and the retrieved chunks,
# and combines them into one big prompt string to send to the LLM.
#
# We also tell the LLM to ONLY answer from the given context.
# If the answer is not in the context, it should say so.
# This is our "guardrail" — prevents hallucination and off-topic answers.
def build_prompt(question: str, chunks: list) -> str:
    # Join all retrieved chunk texts with a separator
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


# ── Main Function: Run Basic RAG Pipeline ─────────────────────────────────────
# This is the function our API will call.
# It runs the complete Basic RAG pipeline:
#   Step 1 → Search ChromaDB for relevant chunks
#   Step 2 → Build a prompt with those chunks
#   Step 3 → Send to LLM and get answer
#   Step 4 → Return the answer + metadata
#
# doc_id   = which document to search in
# question = the user's question
# top_k    = how many chunks to retrieve (default: 5)
def run(doc_id: str, question: str, top_k: int = 5) -> Dict:

    start_time = time.time()   # start timer to measure response speed

    # ── Step 1: Search ChromaDB for top matching chunks ───────────────────────
    # We search in "chunks" collection (overlapping fixed-size chunks)
    retrieved_chunks = search(
        doc_id=doc_id,
        query=question,
        collection_type="chunks",
        top_k=top_k
    )

    if not retrieved_chunks:
        return {
            "pipeline": "basic_rag",
            "answer": "No relevant content found in the document for your question.",
            "model_used": "none",
            "retrieved_chunks": [],
            "response_time_seconds": 0
        }

    # ── Step 2: Build the prompt ──────────────────────────────────────────────
    prompt = build_prompt(question, retrieved_chunks)

    # ── Step 3: Send to LLM and get answer ───────────────────────────────────
    # generate_response() handles Gemini → Groq fallback automatically
    llm_result = generate_response(prompt)

    end_time = time.time()   # stop timer
    response_time = round(end_time - start_time, 2)   # calculate total time in seconds

    # ── Step 4: Return results ────────────────────────────────────────────────
    return {
        "pipeline": "basic_rag",
        "answer": llm_result["answer"],
        "model_used": llm_result["model_used"],
        "retrieved_chunks": retrieved_chunks,   # so dashboard can show what was retrieved
        "response_time_seconds": response_time  # so dashboard can show speed
    }
