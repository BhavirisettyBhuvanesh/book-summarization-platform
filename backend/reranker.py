from typing import List, Dict

def _get_model():
    pass

def rerank(question: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Reranks chunks using the Groq LLM API instead of a local PyTorch model.
    This saves massive amounts of RAM while providing excellent reranking quality.
    """
    if not chunks:
        return []
        
    # If there's only 1 chunk, no need to rerank
    if len(chunks) == 1:
        chunks[0]["rerank_score"] = 1.0
        return chunks
        
    try:
        from llm_handler import call_groq
        
        # Build a prompt asking Groq to rank the chunks
        prompt = (
            f"You are a search relevance ranker. Given the user's question, rank the following text snippets from most relevant to least relevant.\n"
            f"Question: '{question}'\n\n"
        )
        
        for i, chunk in enumerate(chunks):
            prompt += f"--- Snippet {i} ---\n{chunk['content']}\n\n"
            
        prompt += (
            "Analyze how well each snippet answers the question. "
            "Respond ONLY with a comma-separated list of Snippet IDs ordered from most to least relevant (e.g. 2,0,1,3). "
            "Do not output any explanation or other text."
        )
        
        # Call Groq (it's extremely fast)
        response_text = call_groq(prompt)
        
        # Parse the comma-separated list
        # Remove any spaces and extract numbers
        import re
        ranked_indices_str = re.findall(r'\d+', response_text)
        ranked_indices = [int(idx) for idx in ranked_indices_str]
        
        # Filter out any hallucinated indices
        valid_indices = [idx for idx in ranked_indices if 0 <= idx < len(chunks)]
        
        # Add missing indices to the end just in case Groq skipped some
        for i in range(len(chunks)):
            if i not in valid_indices:
                valid_indices.append(i)
                
        # Reorder the chunks based on Groq's output
        reranked_chunks = []
        for rank, original_idx in enumerate(valid_indices):
            chunk = chunks[original_idx]
            # Assign a synthetic score (highest rank gets 1.0, lowest gets near 0)
            chunk["rerank_score"] = round(1.0 - (rank / len(chunks)), 4)
            reranked_chunks.append(chunk)
            
        return reranked_chunks[:top_k]
        
    except Exception as e:
        print(f"[Reranker Fallback] Groq reranking failed: {e}. Falling back to FAISS similarity order.")
        # Fallback to original order if Groq fails or hallucinates
        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = chunk.get("similarity", 0.0)
        return chunks[:top_k]
