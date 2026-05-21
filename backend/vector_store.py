import os
import json
import time
import numpy as np
import faiss
from typing import List, Dict
from google import genai

# ── File paths ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "faiss_store")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Gemini Client Setup ───────────────────────────────────────────────────────
# We use the existing GEMINI_API_KEY from the environment
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        _client = genai.Client(api_key=api_key)
    return _client

# ── Helper: Save/Load Index and Metadata ──────────────────────────────────────
def _get_paths(doc_id: str, collection_type: str):
    folder = os.path.join(DATA_DIR, f"{doc_id}_{collection_type}")
    os.makedirs(folder, exist_ok=True)
    return (
        os.path.join(folder, "index.faiss"),
        os.path.join(folder, "metadata.json")
    )

# ── Main Functions ────────────────────────────────────────────────────────────

def store_chunks(doc_id: str, chunks: List[Dict]):
    """Stores chunks using FAISS and Gemini."""
    _store(doc_id, chunks, "chunks")

def store_pages(doc_id: str, pages: List[Dict]):
    """Stores pages using FAISS and Gemini."""
    _store(doc_id, pages, "pages")

def _store(doc_id: str, items: List[Dict], collection_type: str):
    if not items: return
    
    client = get_client()
    texts = [item["content"] for item in items]
    
    print(f"[VectorStore] Generating Gemini embeddings for {len(texts)} {collection_type}...", flush=True)
    
    embeddings_list = []
    batch_size = 20  # Process in small batches
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        success = False
        retries = 0
        
        while not success:
            try:
                response = client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=batch_texts,
                )
                embeddings_list.extend([emb.values for emb in response.embeddings])
                success = True
                
                # Small pause to avoid hitting the rapid-fire burst limit
                time.sleep(1)
                
            except Exception as e:
                # If we hit the 30K TPM limit, pause for 60s and try again
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if retries > 5:
                        raise Exception("Rate limit exceeded too many times.")
                    print(f"[Rate Limit Hit] Sleeping for 60s before continuing (Batch {i}/{len(texts)})...")
                    time.sleep(60)
                    retries += 1
                else:
                    raise e
                    
    embeddings = np.array(embeddings_list).astype('float32')
    
    # Create FAISS index (gemini-embedding-2 uses 3072 dimensions)
    dimension = 3072 
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index and metadata
    idx_path, meta_path = _get_paths(doc_id, collection_type)
    faiss.write_index(index, idx_path)
    
    # Store everything except the index in metadata
    with open(meta_path, "w") as f:
        json.dump(items, f)
    
    print(f"[FAISS] Stored {len(items)} {collection_type} for doc: {doc_id}")

def search(doc_id: str, query: str, collection_type: str = "chunks", top_k: int = 5) -> List[Dict]:
    """Searches using FAISS and Gemini Embeddings."""
    idx_path, meta_path = _get_paths(doc_id, collection_type)
    
    if not os.path.exists(idx_path):
        return []
        
    client = get_client()
    
    # Generate embedding for the query
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=query,
    )
    query_embedding = np.array([response.embeddings[0].values]).astype('float32')
    
    # Load index and metadata
    index = faiss.read_index(idx_path)
    with open(meta_path, "r") as f:
        metadata = json.load(f)
        
    # Search
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(metadata):
            item = metadata[idx]
            # Match the return format expected by the RAG pipelines
            results.append({
                "content": item["content"],
                "metadata": {k: v for k, v in item.items() if k != "content"},
                "similarity": float(round(1 / (1 + distances[0][i]), 4)) # convert L2 distance to 0-1 similarity
            })
            
    return results

def get_all(doc_id: str, collection_type: str = "chunks") -> List[Dict]:
    """Retrieves all items for a document from FAISS."""
    _, meta_path = _get_paths(doc_id, collection_type)
    
    if not os.path.exists(meta_path):
        return []
        
    with open(meta_path, "r") as f:
        metadata = json.load(f)
        
    return metadata

def delete_document(doc_id: str):
    """Deletes all FAISS files for a document."""
    import shutil
    for c_type in ["chunks", "pages"]:
        folder = os.path.join(DATA_DIR, f"{doc_id}_{c_type}")
        if os.path.exists(folder):
            shutil.rmtree(folder)
    print(f"[FAISS] Deleted data for doc: {doc_id}")

# Provide a dummy preload_model function so main.py doesn't crash when it tries to call it on startup
def preload_model():
    print("[VectorStore] No local model to preload. Gemini API will be used on demand.", flush=True)
