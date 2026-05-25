from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str         # provided by caller; required in practice
    context: list[dict]   # populated by retrieve_node
    answer: str           # populated by answer node

    # Phase 3: theory verification mode
    mode: str                    # "qa" or "theory"
    sub_questions: list[str]     # 2-4 sub-questions from decompose_theory
    evidence: list[dict]         # retrieved chunks keyed by sub_question
    verdict: str                 # "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT"
