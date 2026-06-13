from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., max_length=2000)
    thread_id: Optional[str] = None


class SourceItem(BaseModel):
    source: str
    heading: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    mode: str
    verdict: Optional[str] = None
    thread_id: str
