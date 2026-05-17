# ⬡ DocMind — RAG Technical Documentation Assistant

> A self-corrective Retrieval-Augmented Generation system powered by LangGraph, ChromaDB, and Groq.
> Built for the Express Analytics AI/ML Engineer Intern assignment.

---

## Architecture

```
USER QUESTION
    ↓
[NODE 1] Query Analysis     → rewrite query for better retrieval + classify type
    ↓
[NODE 2] Retrieval          → ChromaDB cosine similarity search (top-5 chunks)
    ↓
[NODE 3] Document Grading   → LLM judges each chunk relevant/irrelevant  ← SELF-CORRECTIVE
    ↓ (conditional routing)
    ├─ relevant docs found  → [NODE 4] Generation → [NODE 5] Hallucination Check → ✓ ANSWER
    ├─ no docs, retry < 3   → rewrite query → retry loop (back to Node 1)
    ├─ TAVILY_KEY set        → [NODE 6] Web Search → Grading (bonus fallback)
    └─ retries exhausted     → [NODE 7] Fallback → graceful "I don't know"
```

### LangGraph StateGraph

The state schema (`app/state.py`) tracks everything between nodes:

| Field | Type | Purpose |
|-------|------|---------|
| `question` | str | Raw user input |
| `rewritten_question` | str | Expanded query from Node 1 |
| `query_type` | str | conceptual / how-to / troubleshooting / api-reference |
| `documents` | list | Raw ChromaDB results |
| `web_search_results` | list | Tavily fallback results |
| `relevant_documents` | list | After grading — only relevant chunks |
| `retry_count` | int | Loop counter (max 3) |
| `should_fallback` | bool | Set True when retries exhausted |
| `answer` | str | Final LLM answer with inline citations |
| `hallucination_score` | str | supported / unsupported / unknown |
| `chat_history` | list | Multi-turn memory per session |

### Chunking Strategy

We use **paragraph-aware chunking** (512 chars, 64 char overlap):
1. Split on `\n\n` (blank lines) — respects natural document structure
2. Merge small paragraphs up to 512 chars — keeps related sentences together
3. 64-char overlap — preserves context at chunk boundaries
4. Minimum chunk length 30 chars — filters noise

Why this beats fixed-size chunking for technical docs: function signatures, parameter descriptions, and code examples often live in the same paragraph and should stay together.

### Embedding Model

`all-MiniLM-L6-v2` (sentence-transformers):
- No API key required — runs locally
- 384-dim embeddings, ~80MB download
- BEIR benchmark F1 ~0.83 — strong on technical English
- ChromaDB configured with **cosine similarity** (more semantically appropriate than L2 for text)

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/your-username/rag-doc-assistant
cd rag-doc-assistant
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Keys

```bash
cp .env.example .env
```

Edit `.env`:
```
GROQ_API_KEY=your_key_here      # Free at console.groq.com
TAVILY_API_KEY=your_key_here    # Optional. Free at app.tavily.com (1000/month)
```

### 3. Ingest documents

```bash
python ingest.py                      # ingests all files in ./docs/
python ingest.py --dir ./my_docs      # custom directory
python ingest.py --url https://...    # ingest from URL
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 5. Start the UI (optional bonus)

```bash
streamlit run streamlit_app.py
```

UI: http://localhost:8501

---

## API Reference

### `POST /query`
Submit a question and get a grounded, cited answer.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I define a Pydantic model with validation?",
    "session_id": "user-123"
  }'
```

Response:
```json
{
  "answer": "To define a Pydantic model, create a class that inherits from `BaseModel` [SOURCE 1: pydantic_guide.md]...",
  "sources": ["pydantic_guide.md"],
  "query_type": "how-to",
  "rewritten_question": "How to create a Pydantic BaseModel class with field validation in Python?",
  "hallucination_score": "supported",
  "used_web_search": false,
  "retry_count": 0
}
```

### `POST /ingest`
Upload a document file.

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@my_doc.md"
```

### `POST /ingest/url`
Ingest from a URL.

```bash
curl -X POST "http://localhost:8000/ingest/url?url=https://docs.pydantic.dev/latest/"
```

### `GET /documents`
List all indexed documents.

```bash
curl http://localhost:8000/documents
```

### `DELETE /documents/{name}`
Remove a document.

```bash
curl -X DELETE http://localhost:8000/documents/my_doc.md
```

### `POST /feedback`
Submit thumbs up/down feedback.

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is FastAPI?",
    "answer": "FastAPI is a modern Python web framework...",
    "rating": "thumbs_up",
    "comment": "Clear and accurate",
    "session_id": "user-123"
  }'
```

### `DELETE /session/{id}`
Clear conversation memory for a session.

```bash
curl -X DELETE http://localhost:8000/session/user-123
```

---

## Bonus Features Implemented

| Feature | Status | Implementation |
|---------|--------|----------------|
| Hallucination Check | ✅ | Self-RAG inspired post-generation verification (`nodes.py:hallucination_check_node`) |
| Web Search Fallback | ✅ | Tavily integration when local docs fail (`nodes.py:web_search_node`) |
| Conversation Memory | ✅ | Per-session chat history in `memory.py`, included in query analysis context |
| Streamlit UI | ✅ | Full-featured dark UI with feedback buttons, doc management, metadata badges |

---

## Document Corpus

Five documents covering the core stack:
- `fastapi_guide.md` — FastAPI complete guide (paths, bodies, DI, middleware)
- `pydantic_guide.md` — Pydantic v2 (models, validators, serialization, settings)
- `langchain_guide.md` — LangChain & LangGraph (chains, LCEL, StateGraph)
- `chromadb_guide.md` — ChromaDB (CRUD, embeddings, filtering, performance)
- `rag_concepts.md` — RAG concepts (chunking, metrics, CRAG, Self-RAG, HyDE)

---

## Design Decisions & Tradeoffs

**Why Groq?** Free tier with very fast inference (Llama3-8b). For production, Claude Haiku or GPT-4o-mini would give better instruction-following.

**Why sentence-transformers over OpenAI embeddings?** No API key needed, no cost, works offline. The tradeoff is slightly lower quality vs `text-embedding-3-large`, but for technical English, `all-MiniLM-L6-v2` is competitive.

**Why in-memory session storage?** Simplicity — the assignment scope doesn't require persistence between server restarts. Production would use Redis with TTL.

**Per-chunk grading vs batch grading?** Per-chunk is more accurate (each chunk judged individually) at the cost of N LLM calls. Batch grading would be faster but risks a single bad chunk dragging down the whole batch.

**What I'd add with more time:**
- Cross-encoder reranking (ms-marco) before generation
- RAGAS evaluation framework for automated quality metrics  
- Streaming SSE responses for real-time feel
- HyDE (Hypothetical Document Embeddings) for better cold-start retrieval
- Persistent feedback store with analytics dashboard
