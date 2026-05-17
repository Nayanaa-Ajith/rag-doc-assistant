"""
FastAPI application — serves the RAG pipeline via HTTP.

Endpoints:
  POST /query       — submit a question, get an answer with citations
  POST /ingest      — upload a document file or ingest from URL
  GET  /documents   — list all indexed documents
  DELETE /documents/{name} — remove a document
  POST /feedback    — submit thumbs up/down + comment
  GET  /health      — system health check
  DELETE /session/{id} — clear conversation memory for a session
"""

import os
import json
import uuid
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.models import (
    QueryRequest, QueryResponse,
    IngestResponse,
    DocumentsResponse, DocumentInfo,
    FeedbackRequest, FeedbackResponse,
    HealthResponse,
)
from app.graph import run_query, WEB_SEARCH_ENABLED
from app.vectorstore import ingest_file, ingest_text, list_documents, delete_document
from app import memory

load_dotenv()

FEEDBACK_FILE = Path(os.getenv("FEEDBACK_FILE", "./feedback_store/feedback.jsonl"))
FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="RAG Technical Documentation Assistant",
    description=(
        "A self-corrective RAG system powered by LangGraph. "
        "Ask questions about indexed technical documentation and get "
        "cited, grounded answers."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── POST /query ────────────────────────────────────────────────────────────────
@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Submit a natural language question. The system will:
    1. Analyze and rewrite the query
    2. Retrieve relevant document chunks
    3. Grade chunks for relevance (self-corrective)
    4. Generate a cited answer
    5. Check for hallucinations (bonus)
    """
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    chat_history = memory.get_history(request.session_id)

    try:
        result = run_query(
            question=request.question,
            session_id=request.session_id,
            chat_history=chat_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    # Store in conversation memory
    memory.add_turn(request.session_id, request.question, result["answer"])

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        query_type=result.get("query_type", ""),
        rewritten_question=result.get("rewritten_question", request.question),
        hallucination_score=result.get("hallucination_score", "unknown"),
        used_web_search=result.get("used_web_search", False),
        retry_count=result.get("retry_count", 0),
    )


# ── POST /ingest ───────────────────────────────────────────────────────────────
@app.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest(file: UploadFile = File(...)):
    """
    Upload a document file (.md, .txt, .html, .py) to index it.
    The file is chunked, embedded, and stored in ChromaDB.
    """
    allowed_extensions = {".md", ".txt", ".html", ".htm", ".py", ".rst", ".json"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed_extensions}",
        )

    content = await file.read()
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode file as text.")

    doc_name = file.filename or f"upload_{uuid.uuid4().hex[:8]}"
    chunks = ingest_text(text, doc_name)

    return IngestResponse(
        message=f"Successfully ingested '{doc_name}'",
        doc_name=doc_name,
        chunks_created=chunks,
    )


@app.post("/ingest/url", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_url(url: str):
    """Fetch content from a URL and ingest it."""
    import requests
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "RAG-Bot/1.0"})
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    content_type = resp.headers.get("content-type", "")
    if "html" in content_type:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove scripts/styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
    else:
        text = resp.text

    doc_name = url.split("//")[-1].split("/")[0] + "_" + url.split("/")[-1][:40]
    chunks = ingest_text(text, doc_name)

    return IngestResponse(
        message=f"Ingested from URL: {url}",
        doc_name=doc_name,
        chunks_created=chunks,
    )


# ── GET /documents ─────────────────────────────────────────────────────────────
@app.get("/documents", response_model=DocumentsResponse, tags=["Documents"])
async def documents():
    """List all documents currently indexed in the vector store."""
    docs = list_documents()
    return DocumentsResponse(
        documents=[DocumentInfo(**d) for d in docs],
        total_documents=len(docs),
        total_chunks=sum(d["chunks"] for d in docs),
    )


# ── DELETE /documents/{name} ───────────────────────────────────────────────────
@app.delete("/documents/{doc_name}", tags=["Documents"])
async def remove_document(doc_name: str):
    """Remove a document and all its chunks from the vector store."""
    deleted = delete_document(doc_name)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found.")
    return {"message": f"Deleted '{doc_name}' ({deleted} chunks removed)"}


# ── POST /feedback ─────────────────────────────────────────────────────────────
@app.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Submit thumbs up/down feedback on an answer."""
    feedback_id = uuid.uuid4().hex

    record = {
        "id": feedback_id,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": request.session_id,
        "question": request.question,
        "answer": request.answer,
        "rating": request.rating,
        "comment": request.comment,
    }

    def _write():
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    background_tasks.add_task(_write)

    return FeedbackResponse(
        message="Feedback recorded — thank you!",
        feedback_id=feedback_id,
    )


# ── DELETE /session/{id} ───────────────────────────────────────────────────────
@app.delete("/session/{session_id}", tags=["Memory"])
async def clear_session(session_id: str):
    """Clear conversation memory for a session."""
    memory.clear_session(session_id)
    return {"message": f"Session '{session_id}' cleared."}


# ── GET /health ────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """System health check."""
    docs = list_documents()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        documents_indexed=len(docs),
        web_search_enabled=WEB_SEARCH_ENABLED,
    )


# ── Root ───────────────────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "message": "RAG Technical Documentation Assistant",
        "docs": "/docs",
        "health": "/health",
    }
