from langgraph.graph import END, StateGraph

from .nodes import (
    answer,
    classify_mode,
    decompose_theory,
    evidence_hunt,
    retrieve_node,
    synthesize_verdict,
)
from .state import AgentState


def _route_after_classify(state: AgentState) -> str:
    return state.get("mode", "qa")


def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("classify_mode", classify_mode)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer)
    graph.add_node("decompose_theory", decompose_theory)
    graph.add_node("evidence_hunt", evidence_hunt)
    graph.add_node("synthesize_verdict", synthesize_verdict)

    graph.set_entry_point("classify_mode")
    graph.add_conditional_edges(
        "classify_mode",
        _route_after_classify,
        {"qa": "retrieve", "theory": "decompose_theory"},
    )

    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    graph.add_edge("decompose_theory", "evidence_hunt")
    graph.add_edge("evidence_hunt", "synthesize_verdict")
    graph.add_edge("synthesize_verdict", END)

    return graph.compile(checkpointer=checkpointer)


def build_graph_no_rag(checkpointer):
    """Same as build_graph but skips the retrieve node — LLM-only baseline."""
    graph = StateGraph(AgentState)

    graph.add_node("answer", answer)

    graph.set_entry_point("answer")
    graph.add_edge("answer", END)

    return graph.compile(checkpointer=checkpointer)
