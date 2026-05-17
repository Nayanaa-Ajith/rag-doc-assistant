"""
LangGraph nodes — fixed grading to be less strict
"""

import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.state import GraphState
from app.vectorstore import search

load_dotenv()

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY", ""),
        )
    return _llm


MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))


def _call_llm(prompt: str) -> str:
    try:
        return _get_llm().invoke(prompt).content.strip()
    except Exception as e:
        return f"ERROR: {e}"


def _parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def query_analysis_node(state: GraphState) -> dict:
    history_ctx = ""
    if state.get("chat_history"):
        recent = state["chat_history"][-4:]
        history_ctx = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
        history_ctx = f"\nChat history:\n{history_ctx}\n"

    prompt = f"""You are a query analysis expert for a technical documentation search system.{history_ctx}
Analyze the user question and return a JSON object with exactly these fields:
- "rewritten": A rewritten version optimized for semantic search. Expand abbreviations, add synonyms.
- "type": One of exactly: conceptual | how-to | troubleshooting | api-reference

User question: {state["question"]}

Return ONLY valid JSON. Example:
{{"rewritten": "How do I install and configure FastAPI with uvicorn server?", "type": "how-to"}}"""

    raw = _call_llm(prompt)
    data = _parse_json(raw)

    return {
        "rewritten_question": data.get("rewritten", state["question"]),
        "query_type": data.get("type", "conceptual"),
    }


def retrieval_node(state: GraphState) -> dict:
    query = state.get("rewritten_question") or state["question"]
    docs = search(query)
    return {"documents": docs}


def web_search_node(state: GraphState) -> dict:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
        query = state.get("rewritten_question") or state["question"]
        results = client.search(query=query, max_results=4)
        web_docs = [
            {
                "content": r.get("content", ""),
                "source": r.get("url", "web"),
                "chunk_index": 0,
                "score": r.get("score", 0.0),
            }
            for r in results.get("results", [])
        ]
        return {"web_search_results": web_docs, "used_web_search": True}
    except Exception as e:
        print(f"Web search failed: {e}")
        return {"web_search_results": [], "used_web_search": False}


def grading_node(state: GraphState) -> dict:
    """
    Grade retrieved chunks. Uses score-based shortcut:
    - Any chunk with cosine similarity >= 0.55 is auto-accepted (no LLM call needed)
    - Lower scored chunks go through LLM grading
    - This prevents the LLM from being overly strict on good matches
    """
    question = state.get("rewritten_question") or state["question"]
    all_docs = list(state.get("documents", [])) + list(state.get("web_search_results", []))
    relevant = []

    SCORE_THRESHOLD = 0.55  # auto-accept above this cosine similarity

    for doc in all_docs:
        score = doc.get("score", 0.0)

        # Auto-accept high-confidence matches
        if score >= SCORE_THRESHOLD:
            print(f"Auto-accepted chunk (score={score}): {doc['source']}")
            relevant.append(doc)
            continue

        # LLM grades borderline chunks
        snippet = doc["content"][:600]
        prompt = f"""Does this document chunk contain information that could help answer the question?
Be generous — if the chunk is even partially related, answer "yes".

Question: {question}

Chunk: {snippet}

Answer "yes" or "no":"""

        answer = _call_llm(prompt).lower()
        if "yes" in answer:
            relevant.append(doc)
            print(f"LLM accepted chunk (score={score}): {doc['source']}")
        else:
            print(f"LLM rejected chunk (score={score}): {doc['source']}")

    retry_count = state.get("retry_count", 0)
    no_relevant = len(relevant) == 0

    if no_relevant:
        retry_count += 1

    # Cap retries at MAX_RETRIES
    should_fallback = no_relevant and retry_count >= MAX_RETRIES

    print(f"Grading result: {len(relevant)} relevant docs, retry_count={retry_count}, fallback={should_fallback}")

    return {
        "relevant_documents": relevant,
        "retry_count": retry_count,
        "should_fallback": should_fallback,
    }


def generation_node(state: GraphState) -> dict:
    docs = state["relevant_documents"]
    question = state["question"]
    query_type = state.get("query_type", "conceptual")

    context_parts = []
    for i, doc in enumerate(docs[:6]):
        source = doc["source"]
        context_parts.append(f"[SOURCE {i+1}: {source}]\n{doc['content']}")
    context = "\n\n---\n\n".join(context_parts)

    sources = list(dict.fromkeys(d["source"] for d in docs))

    type_hints = {
        "how-to": "Give a clear step-by-step answer.",
        "troubleshooting": "Diagnose the problem and provide solutions.",
        "api-reference": "Be precise about parameters, types, and return values.",
        "conceptual": "Explain the concept clearly with examples where helpful.",
    }
    hint = type_hints.get(query_type, "")

    history_ctx = ""
    if state.get("chat_history"):
        recent = state["chat_history"][-4:]
        history_ctx = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
        history_ctx = f"\nPrevious conversation:\n{history_ctx}\n"

    used_web = state.get("used_web_search", False)
    web_note = "\nNote: Some context was retrieved from web search." if used_web else ""

    prompt = f"""You are a precise technical documentation assistant.{history_ctx}
{hint}{web_note}

Answer the question using ONLY the provided context.
Cite sources inline using [SOURCE N] notation.
If the context is insufficient, say so clearly.

Context:
{context}

Question: {question}

Answer:"""

    answer = _call_llm(prompt)
    return {"answer": answer, "sources": sources}


def hallucination_check_node(state: GraphState) -> dict:
    docs = state.get("relevant_documents", [])
    answer = state.get("answer", "")
    if not docs or not answer:
        return {"hallucination_score": "unknown"}

    context = "\n\n".join(d["content"][:400] for d in docs[:4])

    prompt = f"""Is every factual claim in the answer directly supported by the context?

Context:
{context}

Answer:
{answer}

Reply with ONLY one word: "supported" or "unsupported"."""

    score = _call_llm(prompt).lower().strip()
    if "supported" in score and "unsupported" not in score:
        score = "supported"
    elif "unsupported" in score:
        score = "unsupported"
    else:
        score = "unknown"

    return {"hallucination_score": score}


def fallback_node(state: GraphState) -> dict:
    used_web = state.get("used_web_search", False)
    web_note = " I also searched the web but couldn't find relevant results." if used_web else ""

    return {
        "answer": (
            f"I couldn't find relevant information in the indexed documentation "
            f"to answer your question: **\"{state['question']}\"**.{web_note}\n\n"
            "**Suggestions:**\n"
            "- Try rephrasing your question with different keywords\n"
            "- Check if the relevant documentation has been ingested\n"
            "- Use `GET /documents` to see what's currently indexed"
        ),
        "sources": [],
        "hallucination_score": "unknown",
    }