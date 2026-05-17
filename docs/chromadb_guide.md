# ChromaDB — Vector Database Guide

## What is ChromaDB?

ChromaDB is an open-source, AI-native vector database. It stores embeddings alongside their metadata and enables fast similarity search. Perfect for RAG applications.

## Installation

```bash
pip install chromadb
```

## Quick Start

```python
import chromadb

# In-memory (ephemeral)
client = chromadb.EphemeralClient()

# Persistent (saves to disk)
client = chromadb.PersistentClient(path="./chroma_db")

# Create a collection
collection = client.create_collection(name="my_docs")

# Add documents (ChromaDB auto-embeds if no embeddings provided)
collection.add(
    documents=["doc one", "doc two", "doc three"],
    ids=["id1", "id2", "id3"],
    metadatas=[{"source": "a"}, {"source": "b"}, {"source": "c"}],
)

# Query
results = collection.query(query_texts=["doc"], n_results=2)
```

## Using Custom Embeddings

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
docs = ["Hello world", "Goodbye world"]
embeddings = model.encode(docs).tolist()

collection = client.create_collection(
    name="my_docs",
    metadata={"hnsw:space": "cosine"}  # cosine similarity (default is l2)
)

collection.add(
    documents=docs,
    embeddings=embeddings,
    ids=["doc1", "doc2"],
)

# Query with embedding
query_embedding = model.encode(["Hello"]).tolist()
results = collection.query(query_embeddings=query_embedding, n_results=1)
```

## Distance Metrics

- `l2` (default): Euclidean distance. Lower = more similar.
- `cosine`: Cosine similarity. Best for text embeddings.
- `ip`: Inner product. Use when embeddings are normalized.

Set via: `metadata={"hnsw:space": "cosine"}`

## CRUD Operations

```python
# Add
collection.add(documents=["text"], ids=["id1"])

# Upsert (add or update)
collection.upsert(documents=["updated text"], ids=["id1"])

# Get by ID
collection.get(ids=["id1"])

# Get all
collection.get(include=["documents", "metadatas", "embeddings"])

# Delete by ID
collection.delete(ids=["id1"])

# Count
collection.count()
```

## Metadata Filtering

```python
# Filter by metadata during query
results = collection.query(
    query_texts=["machine learning"],
    n_results=5,
    where={"source": "arxiv"},          # exact match
    where_document={"$contains": "neural"},  # content contains
)

# More filter operators
where={"year": {"$gte": 2023}}         # greater than or equal
where={"$and": [{"source": "a"}, {"year": {"$gt": 2022}}]}
where={"source": {"$in": ["a", "b"]}}  # in list
```

## Managing Collections

```python
# List all collections
client.list_collections()

# Get existing collection
collection = client.get_collection("my_docs")

# Get or create
collection = client.get_or_create_collection("my_docs")

# Delete a collection
client.delete_collection("my_docs")
```

## Performance Tips

1. **Batch inserts**: Add documents in batches of 100-1000 for better throughput.
2. **Persist path on SSD**: ChromaDB's HNSW index is I/O intensive.
3. **Set hnsw:ef_construction**: Higher = better recall, slower build. Default: 100.
4. **Use cosine space** for text embeddings — it's more semantically appropriate than L2.

```python
collection = client.create_collection(
    name="docs",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,
        "hnsw:search_ef": 100,
    }
)
```

## Troubleshooting

**Error**: `Collection already exists`
**Fix**: Use `get_or_create_collection` instead of `create_collection`.

**Error**: `Embedding dimension mismatch`
**Fix**: Ensure you always use the same embedding model for a collection. Different models produce different dimensions.

**Error**: Slow queries on large collections
**Fix**: Increase `hnsw:search_ef` for better recall, or decrease for speed.

**Slow inserts**
**Fix**: Batch documents and use `upsert` in chunks of 500.
