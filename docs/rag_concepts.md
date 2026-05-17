# RAG — Retrieval Augmented Generation Concepts

## What is RAG?

Retrieval-Augmented Generation (RAG) is a technique that improves LLM responses by:
1. Retrieving relevant documents from a knowledge base
2. Including those documents as context in the LLM prompt
3. Generating a response grounded in the retrieved information

RAG solves key LLM limitations:
- **Hallucination**: LLMs generate plausible-sounding but false information. RAG grounds answers in facts.
- **Knowledge cutoff**: LLMs don't know about recent events. RAG gives them access to up-to-date docs.
- **Domain specificity**: LLMs lack your private data. RAG adds your proprietary knowledge.

## Basic RAG Pipeline

```
User Question
    ↓
Query Analysis (rewrite, classify)
    ↓
Embedding (convert question to vector)
    ↓
Similarity Search (find top-k chunks)
    ↓
Context Assembly (combine chunks)
    ↓
LLM Generation (answer + citations)
    ↓
Response
```

## Chunking Strategies

### Fixed-size chunking
Simple split by character count:
```python
chunks = [text[i:i+512] for i in range(0, len(text), 512-64)]  # 64 char overlap
```
Pros: Simple, predictable. Cons: Splits mid-sentence, loses context.

### Paragraph-aware chunking
Split on `\n\n`, then merge small paragraphs:
```python
paragraphs = text.split("\n\n")
# Merge until size limit, then emit chunk
```
Pros: Respects natural structure. Cons: Variable chunk sizes.

### Recursive character splitting
Try large separators first (`\n\n`, `\n`, `.`, ` `):
```python
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
```
Best general-purpose approach for technical docs.

### Semantic chunking
Group sentences by semantic similarity:
- More complex but produces more coherent chunks
- Use `sentence-transformers` to detect topic boundaries

## Embedding Models

| Model | Dimensions | Size | Speed | Quality |
|-------|-----------|------|-------|---------|
| all-MiniLM-L6-v2 | 384 | 80MB | Fast | Good |
| all-mpnet-base-v2 | 768 | 420MB | Medium | Better |
| text-embedding-3-small (OpenAI) | 1536 | API | Fast | Excellent |
| text-embedding-3-large (OpenAI) | 3072 | API | Slow | Best |

For technical docs with no API budget, `all-MiniLM-L6-v2` is the recommended default.

## Self-Corrective RAG (CRAG)

CRAG adds a grading step that evaluates retrieved documents:

```
Retrieve → Grade → [Relevant?]
                      Yes → Generate
                      No  → Rewrite query → Re-retrieve (up to N retries)
                      Exhausted → Fallback (web search or "don't know")
```

Benefits:
- Reduces irrelevant context passed to the LLM
- Forces the system to actively seek better information
- Provides graceful degradation

## Adaptive RAG

Routes queries to different pipelines based on query type:
- Simple factual → direct retrieval
- Complex multi-hop → agent with iterative retrieval
- Unclear → web search first

## Self-RAG

Adds a hallucination verification step:

```
Generate answer
    ↓
Is the answer supported by the retrieved context?
    Yes → Return answer
    No  → Regenerate with different framing or flag as uncertain
```

Implementation:
```python
def check_hallucination(answer: str, context: str, llm) -> bool:
    prompt = f"Is this answer supported by the context?\nContext: {context}\nAnswer: {answer}\nReply yes or no."
    result = llm.invoke(prompt).content.lower()
    return "yes" in result
```

## Retrieval Quality Metrics

- **Precision@k**: Of the top-k retrieved docs, what fraction is relevant?
- **Recall@k**: Of all relevant docs, what fraction did we retrieve?
- **MRR**: Mean Reciprocal Rank — how high is the first relevant doc?
- **NDCG**: Normalized Discounted Cumulative Gain — accounts for position

## Query Rewriting Techniques

### HyDE (Hypothetical Document Embeddings)
Generate a hypothetical answer first, then search for documents similar to it:
```python
hyp_answer = llm.invoke(f"Write a hypothetical answer to: {question}")
docs = vectorstore.search(hyp_answer)  # Search by hypothetical answer
```

### Query expansion
Add synonyms and related terms:
```python
expanded = llm.invoke(f"Expand this search query with synonyms: {question}")
```

### Multi-query retrieval
Generate multiple query variants and merge results:
```python
queries = llm.invoke(f"Generate 3 different phrasings of: {question}")
all_docs = [vectorstore.search(q) for q in queries]
unique_docs = deduplicate(all_docs)
```

## Context Window Management

LLMs have context limits. With many retrieved chunks:
1. **Truncate**: Keep only top-k by score
2. **Summarize**: Compress each chunk before including
3. **Map-reduce**: Answer per chunk, then combine answers
4. **Rerank**: Use a cross-encoder model to reorder chunks before truncating

## Citations and Grounding

Best practice for citations:
```python
context = "\n\n".join([f"[SOURCE {i+1}: {doc.source}]\n{doc.content}" for i, doc in enumerate(docs)])
prompt = f"Answer using [SOURCE N] citations.\n\nContext:\n{context}\n\nQuestion: {question}"
```

This lets the LLM produce answers like:
"FastAPI is a modern Python web framework [SOURCE 1: fastapi_guide.md] that supports async operations [SOURCE 2: async_guide.md]."
