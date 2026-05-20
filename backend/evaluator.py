import os
import json
import re
from typing import Dict
from llm_handler import generate_response

def evaluate_pipeline(pipeline_result: Dict, question: str) -> Dict:
    """
    Fast AI Scorer: Uses a single LLM call to get multiple quality metrics.
    Much faster than RAGAS and avoids rate limit issues.
    """
    answer = pipeline_result.get("answer", "")
    
    # Get retrieved context
    chunks = (
        pipeline_result.get("retrieved_chunks") or
        pipeline_result.get("retrieved_pages") or
        []
    )
    context_texts = "\n---\n".join([str(chunk.get("content", "")) for chunk in chunks[:3]])

    if not answer or not context_texts:
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "retrieval_diversity": 0.0,
            "overall_score": 0.0
        }

    print(f"[Evaluator] Fast-Scoring pipeline: {pipeline_result.get('pipeline')}...")

    # Single-shot prompt for all metrics - demanding high precision
    prompt = f"""Evaluate the following RAG (Retrieval-Augmented Generation) response based on the provided context.
Be extremely critical and provide EXACT scores from 0.00 to 1.00 based on the evidence.

Metrics:
1. Faithfulness: (Is every claim in the answer supported by the context?)
2. Answer Relevancy: (Does the answer directly and fully address the question?)
3. Retrieval Diversity: (Does the context come from diverse parts of the doc or just one spot?)

Return ONLY a JSON object: {{"faithfulness": float, "answer_relevancy": float, "retrieval_diversity": float}}

QUESTION: {question}
CONTEXT: {context_texts}
ANSWER: {answer}

JSON:"""

    try:
        res = generate_response(prompt)
        raw_text = res.get("answer", "{}")
        
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            scores = json.loads(match.group(0))
            print(f"[DEBUG] AI Returned: {match.group(0)}")
        else:
            print(f"[Evaluator Warning] No JSON found in response: {raw_text}")
            scores = {}
            
    except Exception as e:
        print(f"[Evaluator Error] {e}")
        scores = {}

    # Extract exact values with flexible key matching
    def get_score(keys, default=0.0):
        for k in keys:
            for actual_k in scores.keys():
                if k.lower() in actual_k.lower():
                    return float(scores[actual_k])
        return default

    f = get_score(["faithfulness", "faithful"], 0.0)
    r = get_score(["relevancy", "relevant"], 0.0)
    d = get_score(["diversity", "diverse"], 0.0)
    
    print(f"--- SCORES [{pipeline_result.get('pipeline')}]: F:{f}, R:{r}, D:{d} ---")
    
    return {
        "faithfulness": round(f, 2),
        "answer_relevancy": round(r, 2),
        "retrieval_diversity": round(d, 2),
        "overall_score": round((f + r + d) / 3, 2)
    }
