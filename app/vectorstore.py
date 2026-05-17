"""
Vector store — ChromaDB 1.5+ with absolute path fix
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Use absolute path so it works from ANY working directory
_BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = str(_BASE_DIR / "chroma_db")
TOP_K = int(os.getenv("TOP_K_RESULTS", "5"))

print(f"ChromaDB path: {CHROMA_PATH}")
print("Loading embedding model...")
_embed_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model ready.")

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"}
)
print(f"Collection has {_collection.count()} chunks loaded.")


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
                current = current[-overlap:] + "\n\n" + para if overlap else para
            else:
                while len(para) > chunk_size:
                    chunks.append(para[:chunk_size])
                    para = para[chunk_size - overlap:]
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) > 30]


def ingest_text(text: str, doc_name: str) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embeddings = _embed_model.encode(chunks, show_progress_bar=False).tolist()
    ids = [f"{doc_name}::{i}" for i in range(len(chunks))]
    metadatas = [{"source": doc_name, "chunk_index": i} for i in range(len(chunks))]
    _collection.upsert(documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)
    return len(chunks)


def ingest_file(filepath: str, doc_name: str = None) -> int:
    path = Path(filepath)
    doc_name = doc_name or path.name
    text = path.read_text(encoding="utf-8", errors="replace")
    count = ingest_text(text, doc_name)
    print(f"✓ Ingested '{doc_name}' → {count} chunks")
    return count


def search(query: str, top_k: int = TOP_K) -> List[dict]:
    count = _collection.count()
    if count == 0:
        print("WARNING: Collection is empty!")
        return []
    print(f"Searching {count} chunks for: {query[:60]}...")
    embedding = _embed_model.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=embedding,
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )
    docs = [
        {
            "content": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "score": round(1 - dist, 4),
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
    print(f"Found {len(docs)} chunks, top score: {docs[0]['score'] if docs else 'N/A'}")
    return docs


def list_documents() -> List[dict]:
    all_meta = _collection.get(include=["metadatas"])["metadatas"]
    counts: dict = {}
    for m in all_meta:
        src = m["source"]
        counts[src] = counts.get(src, 0) + 1
    return [{"name": name, "chunks": count} for name, count in sorted(counts.items())]


def delete_document(doc_name: str) -> int:
    all_items = _collection.get(include=["metadatas"])
    ids_to_delete = [
        id_ for id_, meta in zip(all_items["ids"], all_items["metadatas"])
        if meta["source"] == doc_name
    ]
    if ids_to_delete:
        _collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)