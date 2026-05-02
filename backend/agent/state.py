from typing import TypedDict


class AgentState(TypedDict):
    question: str
    context: list[dict]   # chunks returned by the retrieve node
    answer: str
