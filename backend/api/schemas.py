from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
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
