from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str         # provided by caller; required in practice
    context: list[dict]   # populated by retrieve_node
    answer: str           # populated by answer node
