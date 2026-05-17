"""
GraphState — fixed for LangGraph 0.2.x compatibility.
All fields use total=False to prevent LangGraph from trying len() on ints.
"""

from typing import TypedDict, List, Any, Optional


class GraphState(TypedDict, total=False):
    question: str
    session_id: str
    rewritten_question: str
    query_type: str
    documents: List[Any]
    web_search_results: List[Any]
    relevant_documents: List[Any]
    retry_count: int
    should_fallback: bool
    used_web_search: bool
    answer: str
    sources: List[str]
    hallucination_score: str
    chat_history: List[Any]