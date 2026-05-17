"""
GraphState — the single data structure that flows through every LangGraph node.

Design decisions:
- retry_count tracks how many times we've re-retrieved without relevant docs.
- should_fallback is set True when retry_count >= MAX_RETRIES.
- web_search_results holds Tavily results when the local store has nothing.
- chat_history supports multi-turn conversation memory (bonus feature).
"""

from typing import TypedDict, List, Optional


class GraphState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────────
    question: str                        # Raw user question
    session_id: str                      # For conversation memory

    # ── Query Analysis ─────────────────────────────────────────────────────────
    rewritten_question: str              # Expanded/clarified query
    query_type: str                      # conceptual | how-to | troubleshooting | api-reference

    # ── Retrieval ──────────────────────────────────────────────────────────────
    documents: List[dict]                # Raw retrieved chunks [{content, source, chunk_index}]
    web_search_results: List[dict]       # Tavily results if local store empty

    # ── Grading ────────────────────────────────────────────────────────────────
    relevant_documents: List[dict]       # Filtered to relevant only
    retry_count: int                     # Number of re-retrieval attempts
    should_fallback: bool                # True when retries exhausted
    used_web_search: bool                # True if Tavily was used

    # ── Generation ─────────────────────────────────────────────────────────────
    answer: str                          # Final answer with inline citations
    sources: List[str]                   # Unique source doc names
    hallucination_score: str             # supported | unsupported | unknown

    # ── Memory ─────────────────────────────────────────────────────────────────
    chat_history: List[dict]             # [{role: user|assistant, content: str}]
