from langgraph.graph import END, StateGraph

from .nodes import answer, retrieve_node, route
from .state import AgentState


def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("route", route)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer)

    graph.set_entry_point("route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)

    return graph.compile(checkpointer=checkpointer)


def build_graph_no_rag(checkpointer):
    """Same as build_graph but skips the retrieve node — LLM-only baseline."""
    graph = StateGraph(AgentState)

    graph.add_node("route", route)
    graph.add_node("answer", answer)

    graph.set_entry_point("route")
    graph.add_edge("route", "answer")
    graph.add_edge("answer", END)

    return graph.compile(checkpointer=checkpointer)
