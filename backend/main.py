import os
import sys
import json
import shutil
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend folder to path
sys.path.append(os.path.dirname(__file__))

# Import RAG pipeline modules FIRST to prevent Windows DLL conflicts with PyTorch
print("[Startup] Loading RAG modules...", flush=True)
from document_processor import process_document
from vector_store import store_chunks, store_pages, delete_document
from evaluator import evaluate_pipeline
import pipelines.basic_rag as basic_rag
import pipelines.page_index_rag as page_index_rag
import pipelines.hybrid_rag as hybrid_rag
print("[Startup] All modules loaded.", flush=True)

# FastAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# Import our own files
import database, models, auth_utils
from database import engine, get_db

# Create Database Tables on startup
models.Base.metadata.create_all(bind=engine)



# ── File paths ─────────────────────────────────────────────────────────────────
DATA_DIR      = Path(__file__).parent.parent / "data"
UPLOAD_DIR    = DATA_DIR / "uploads"
METADATA_FILE = DATA_DIR / "documents.json"

# Create folders
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Request Model for /query ───────────────────────────────────────────────────
class QueryRequest(BaseModel):
    doc_id: str
    question: str

# ── Helper: Load & Save Document Metadata ─────────────────────────────────────
def load_metadata() -> list:
    if not METADATA_FILE.exists():
        return []
    with open(METADATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_metadata(docs: list):
    with open(METADATA_FILE, "w") as f:
        json.dump(docs, f, indent=2)

# ── FastAPI App Setup ──────────────────────────────────────────────────────────
app = FastAPI(title="Book Summarization Platform", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    print("[Startup] Triggering ML model preload...", flush=True)
    from vector_store import preload_model
    preload_model()
    print("[Startup] Server fully ready to accept requests.", flush=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# CORS Setup - Allow all origins so Vercel can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- CURRENT USER HELPER ---
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

from fastapi import Depends, HTTPException, status, Form

# --- AUTH ROUTES ---
@app.post("/auth/register")
async def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth_utils.get_password_hash(password)
    new_user = models.User(email=email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth_utils.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer", "email": new_user.email}

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "email": user.email}

# --- HISTORY ROUTE ---
@app.get("/history")
async def get_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(models.QueryHistory).filter(models.QueryHistory.user_id == current_user.id).order_by(models.QueryHistory.timestamp.desc()).all()
    # Convert SQLAlchemy objects to dicts for JSON serialization
    results = []
    for h in history:
        results.append({
            "id": h.id,
            "question": h.question,
            "answer": h.answer,
            "pipeline_used": h.pipeline_used,
            "scores": json.loads(h.scores_json) if h.scores_json else {},
            "timestamp": h.timestamp.isoformat()
        })
    return results

# ── Request Model for /query ───────────────────────────────────────────────────
class QueryRequest(BaseModel):
    doc_id: str
    question: str

# ── Helper: Load & Save Document Metadata ─────────────────────────────────────
def load_metadata() -> list:
    if not METADATA_FILE.exists():
        return []
    with open(METADATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_metadata(docs: list):
    with open(METADATA_FILE, "w") as f:
        json.dump(docs, f, indent=2)

def process_and_store_background(file_path: str, filename: str, doc_id: str):
    try:
        print(f"[Background] Starting processing for: {filename}")
        doc_data = process_document(file_path)

        # Store chunks and pages using the new stable FAISS engine
        store_chunks(doc_id, doc_data["chunks"])
        store_pages(doc_id, doc_data["pages"])

        # Save document metadata to our JSON file
        docs = load_metadata()
        docs.append({
            "doc_id":       doc_id,
            "filename":     filename,
            "total_pages":  doc_data["total_pages"],
            "total_chunks": doc_data["total_chunks"],
            "file_path":    file_path
        })
        save_metadata(docs)
        print(f"[Background] Finished processing for: {filename}")
    except Exception as e:
        print(f"!!! BACKGROUND CRASH: {str(e)}")
        import traceback
        traceback.print_exc()
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):

    # Validate that the uploaded file is a PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Generate a unique ID for this document
    doc_id = str(uuid.uuid4())[:8]

    # Save the uploaded file to our uploads folder
    save_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Queue the heavy embedding work in the background!
    background_tasks.add_task(process_and_store_background, str(save_path), file.filename, doc_id)

    return {
        "message":      "Document uploaded and processing in background!",
        "doc_id":       doc_id,
        "filename":     file.filename,
        "total_pages":  "Processing...",
        "total_chunks": "Processing..."
    }


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 2: GET /documents
# ══════════════════════════════════════════════════════════════════════════════
# Returns a list of all uploaded documents.
@app.get("/documents")
def list_documents(current_user: models.User = Depends(get_current_user)):
    docs = load_metadata()
    return {"documents": docs}


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 3: DELETE /documents/{doc_id}
# ══════════════════════════════════════════════════════════════════════════════
# Deletes a document: removes the PDF file, ChromaDB collections, and metadata.
@app.delete("/documents/{doc_id}")
def delete_doc(doc_id: str, current_user: models.User = Depends(get_current_user)):
    docs = load_metadata()

    # Find the document in our metadata
    doc = next((d for d in docs if d["doc_id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete the PDF file from disk
    file_path = Path(doc["file_path"])
    if file_path.exists():
        os.remove(file_path)

    # Delete the ChromaDB collections (chunks + pages)
    delete_document(doc_id)

    # Remove from metadata and save
    docs = [d for d in docs if d["doc_id"] != doc_id]
    save_metadata(docs)

    return {"message": f"Document '{doc['filename']}' deleted successfully."}


# The main route: runs all 3 pipelines, evaluates each, returns full comparison.
@app.post("/query")
async def query_document(
    request: QueryRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    doc_id   = request.doc_id
    question = request.question

    # Check that the document exists
    docs = load_metadata()
    doc = next((d for d in docs if d["doc_id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    print(f"\n[Query] Question: {question} (User: {current_user.email})")
    
    def log_step(msg):
        print(f"[DEBUG] {msg}", flush=True)
    
    try:
        # ── Run all 3 pipelines ───────────────────────────────────────────────────
        log_step("Starting Pipeline 1: Basic RAG...")
        result1 = basic_rag.run(doc_id, question)
        log_step("Starting Pipeline 2: Page Indexing RAG...")
        result2 = page_index_rag.run(doc_id, question)
        log_step("Starting Pipeline 3: Hybrid RAG...")
        result3 = hybrid_rag.run(doc_id, question)

        # ── Evaluate all 3 pipelines ──────────────────────────────────────────────
        log_step("Evaluating results...")
        scores1 = evaluate_pipeline(result1, question)
        scores2 = evaluate_pipeline(result2, question)
        scores3 = evaluate_pipeline(result3, question)

        # ── Find the best pipeline ────────────────────────
        pipeline_scores = {
            "basic_rag":      scores1["overall_score"],
            "page_index_rag": scores2["overall_score"],
            "hybrid_rag":     scores3["overall_score"],
        }
        best_pipeline_id = max(pipeline_scores, key=pipeline_scores.get)
        
        # Determine winning answer
        best_res = {"basic_rag": result1, "page_index_rag": result2, "hybrid_rag": result3}[best_pipeline_id]
        best_scores = {"basic_rag": scores1, "page_index_rag": scores2, "hybrid_rag": scores3}[best_pipeline_id]

        # ── SAVE TO HISTORY ──
        new_history = models.QueryHistory(
            user_id=current_user.id,
            question=question,
            answer=best_res.get("answer", ""),
            pipeline_used=best_pipeline_id,
            scores_json=json.dumps(best_scores)
        )
        db.add(new_history)
        db.commit()

        # ── Return complete results ───────────────────────────────────────────────
        result_data = {
            "question":     question,
            "best_pipeline": best_pipeline_id,
            "results": {
                "basic_rag":      {**result1, "scores": scores1},
                "page_index_rag": {**result2, "scores": scores2},
                "hybrid_rag":     {**result3, "scores": scores3}
            }
        }
        return JSONResponse(content=result_data)
    except Exception as e:
        log_step(f"CRASH: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Run the server
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
