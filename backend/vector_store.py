import os
import json

# Force offline mode BEFORE importing sentence_transformers
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import numpy as np
import faiss
from typing import List, Dict
from sentence_transformers import SentenceTransformer

# ── File paths ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "faiss_store")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Global Model (Loaded on demand) ───────────────────────────────────────────
_model = None

def preload_model():
    """Call this during FastAPI startup to ensure the model is loaded before requests."""
    global _model
    if _model is None:
        print("[VectorStore] Loading embedding model (this takes a moment)...", flush=True)
        _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        print("[VectorStore] Model ready.", flush=True)

def _get_model():
    global _model
    if _model is None:
        preload_model()
    return _model

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
    """Stores chunks using FAISS."""
    _store(doc_id, chunks, "chunks")

def store_pages(doc_id: str, pages: List[Dict]):
    """Stores pages using FAISS."""
    _store(doc_id, pages, "pages")

def _store(doc_id: str, items: List[Dict], collection_type: str):
    if not items: return
    
    model = _get_model()
    texts = [item["content"] for item in items]
    embeddings = model.encode(texts, convert_to_numpy=True).astype('float32')
    
    # Create FAISS index
    dimension = embeddings.shape[1]
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
    """Searches using FAISS."""
    idx_path, meta_path = _get_paths(doc_id, collection_type)
    
    if not os.path.exists(idx_path):
        return []
        
    model = _get_model()
    query_embedding = model.encode([query], convert_to_numpy=True).astype('float32')
    
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
