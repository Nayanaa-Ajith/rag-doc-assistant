from typing import TypedDict, List, Any, Annotated


def _replace(old, new):
    return new


class GraphState(TypedDict):
    question: Annotated[str, _replace]
    session_id: Annotated[str, _replace]
    rewritten_question: Annotated[str, _replace]
    query_type: Annotated[str, _replace]
    documents: Annotated[List[Any], _replace]
    web_search_results: Annotated[List[Any], _replace]
    relevant_documents: Annotated[List[Any], _replace]
    retry_count: Annotated[int, _replace]
    should_fallback: Annotated[bool, _replace]
    used_web_search: Annotated[bool, _replace]
    answer: Annotated[str, _replace]
    sources: Annotated[List[str], _replace]
    hallucination_score: Annotated[str, _replace]
    chat_history: Annotated[List[Any], _replace]