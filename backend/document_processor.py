import os
import fitz  # PyMuPDF
from typing import List, Dict


# ── Function 1: Extract text page by page ─────────────────────────────────────
# This function opens the PDF and reads each page separately.
# It returns a list where each item = one page with its text and page number.
# Used by: Pipeline 2 (Page Indexing RAG)
def extract_text_by_pages(pdf_path: str) -> List[Dict]:
    doc = fitz.open(pdf_path)      # open the PDF file
    pages = []

    for i, page in enumerate(doc):
        # FREE TIER PROTECTION: Limit to first 15 pages to prevent exceeding 
        # Gemini's strict 30,000 Tokens-Per-Minute quota on free accounts.
        if i >= 15:
            print("[Info] Stopping at page 15 to stay within Gemini Free Tier limits.")
            break
            
        text = page.get_text()    # extract raw text from this page

        # Some pages might be images (scanned PDFs) and have no text
        if text and text.strip():
            pages.append({
                "page_number": i + 1,     # page numbers start from 1, not 0
                "content": text.strip()   # remove extra whitespace
            })

    doc.close()
    return pages


# ── Function 2: Chunk text with overlap ───────────────────────────────────────
# This function takes a long text and splits it into smaller chunks.
# chunk_size  = how many words per chunk (default: 500)
# overlap     = how many words to share between consecutive chunks (default: 50)
#
# Example with chunk_size=10, overlap=3:
#   words = [w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12]
#   Chunk 1: w1  → w10
#   Chunk 2: w8  → w17   ← starts 3 words before Chunk 1 ends (overlap)
#   Chunk 3: w15 → w24   ← same pattern
#
# Used by: Pipeline 1 (Basic RAG) and Pipeline 3 (Hybrid RAG)
def chunk_text_with_overlap(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict]:

    words = text.split()      # split full text into individual words
    chunks = []
    chunk_index = 0
    start = 0                 # starting word index for current chunk

    while start < len(words):
        end = start + chunk_size                     # ending word index for current chunk
        chunk_words = words[start:end]               # grab the words for this chunk
        chunk_text  = " ".join(chunk_words)          # join words back into a string

        chunks.append({
            "chunk_index": chunk_index,              # which chunk number this is
            "content": chunk_text,                   # the actual text of this chunk
            "word_count": len(chunk_words)           # how many words in this chunk
        })

        chunk_index += 1
        start = end - overlap   # move start back by 'overlap' words for next chunk
                                # this creates the shared/overlapping region

    return chunks


# ── Function 3: Process Document (main function) ──────────────────────────────
# This is the function that our API will call when a user uploads a PDF.
# It does everything:
#   1. Reads the PDF page by page
#   2. Combines all pages into one big text
#   3. Creates overlapping chunks from that text
#   4. Returns both pages AND chunks, ready for all 3 pipelines
def process_document(pdf_path: str) -> Dict:

    # Step 1: Extract pages (used directly by Pipeline 2)
    pages = extract_text_by_pages(pdf_path)

    if not pages:
        raise ValueError("Could not extract any text from this PDF. It may be a scanned image PDF.")

    # Step 2: Combine all page texts into one big text
    # (used to create chunks for Pipeline 1 and Pipeline 3)
    full_text = "\n".join([page["content"] for page in pages])

    # Step 3: Create overlapping chunks from the full text
    chunks = chunk_text_with_overlap(
        text=full_text,
        chunk_size=500,   # each chunk = ~500 words
        overlap=50        # 50 words shared between consecutive chunks
    )

    # Step 4: Get just the filename (not the full path) for display purposes
    filename = os.path.basename(pdf_path)

    return {
        "filename": filename,           # e.g. "mybook.pdf"
        "total_pages": len(pages),      # how many pages the PDF has
        "total_chunks": len(chunks),    # how many chunks we created
        "pages": pages,                 # list of page objects (for Pipeline 2)
        "chunks": chunks                # list of chunk objects (for Pipeline 1 & 3)
    }
