"""
LangGraph StateGraph — fixed for Streamlit Cloud deployment.
Graph is built lazily (on first query) so API keys are set before initialization.
"""

import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")
WEB_SEARCH_ENABLED = bool(TAVILY_KEY and TAVILY_KEY != "your_tavily_api_key_here")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

_rag_graph = None


def _build_graph():
    from langgraph.graph import StateGraph, END
    from app.state import GraphState
    from app.nodes import (
        query_analysis_node,
        retrieval_node,
        web_search_node,
        grading_node,
        generation_node,
        hallucination_check_node,
        fallback_node,
    )

    def route_after_grading(state) -> str:
        if state.get("should_fallback"):
            return "fallback"
        if state.get("relevant_documents"):
            return "generate"
        retry = state.get("retry_count", 0)
        if WEB_SEARCH_ENABLED and not state.get("used_web_search") and retry >= 1:
            return "web_search"
        return "rewrite"

    g = StateGraph(GraphState)

    g.add_node("query_analysis", query_analysis_node)
    g.add_node("retrieval", retrieval_node)
    g.add_node("web_search", web_search_node)
    g.add_node("grading", grading_node)
    g.add_node("generation", generation_node)
    g.add_node("hallucination_check", hallucination_check_node)
    g.add_node("fallback", fallback_node)

    g.set_entry_point("query_analysis")

    g.add_edge("query_analysis", "retrieval")
    g.add_edge("retrieval", "grading")
    g.add_edge("web_search", "grading")
    g.add_edge("generation", "hallucination_check")
    g.add_edge("hallucination_check", END)
    g.add_edge("fallback", END)

    g.add_conditional_edges(
        "grading",
        route_after_grading,
        {
            "generate": "generation",
            "web_search": "web_search",
            "fallback": "fallback",
            "rewrite": "query_analysis",
        },
    )

    return g.compile()


def _get_graph():
    global _rag_graph
    if _rag_graph is None:
        _rag_graph = _build_graph()
    return _rag_graph


def run_query(
    question: str,
    session_id: str = "default",
    chat_history: list = None,
) -> dict:
    initial_state = {
        "question": question,
        "session_id": session_id,
        "rewritten_question": "",
        "query_type": "",
        "documents": [],
        "web_search_results": [],
        "relevant_documents": [],
        "retry_count": 0,
        "should_fallback": False,
        "used_web_search": False,
        "answer": "",
        "sources": [],
        "hallucination_score": "unknown",
        "chat_history": chat_history or [],
    }
    result = _get_graph().invoke(initial_state)
    return dict(result)