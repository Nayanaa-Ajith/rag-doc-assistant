"""Pydantic request/response models for FastAPI endpoints."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="User's question")
    session_id: str = Field(default="default", description="Session ID for conversation memory")

    model_config = {"json_schema_extra": {"example": {"question": "How do I define a Pydantic model?", "session_id": "user-123"}}}


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    query_type: str
    rewritten_question: str
    hallucination_score: str
    used_web_search: bool
    retry_count: int


class IngestResponse(BaseModel):
    message: str
    doc_name: str
    chunks_created: int


class DocumentInfo(BaseModel):
    name: str
    chunks: int


class DocumentsResponse(BaseModel):
    documents: List[DocumentInfo]
    total_documents: int
    total_chunks: int


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    comment: Optional[str] = Field(default=None, max_length=1000)
    session_id: str = Field(default="default")

    model_config = {"json_schema_extra": {"example": {
        "question": "How do I install FastAPI?",
        "answer": "Use pip install fastapi",
        "rating": "thumbs_up",
        "comment": "Very clear answer!",
        "session_id": "user-123",
    }}}


class FeedbackResponse(BaseModel):
    message: str
    feedback_id: str


class HealthResponse(BaseModel):
    status: str
    version: str
    documents_indexed: int
    web_search_enabled: bool
