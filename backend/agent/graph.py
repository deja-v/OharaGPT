from langgraph.graph import END, StateGraph

from .nodes import answer, route
from .state import AgentState


def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("route", route)
    graph.add_node("answer", answer)

    graph.set_entry_point("route")
    graph.add_edge("route", "answer")
    graph.add_edge("answer", END)

    return graph.compile(checkpointer=checkpointer)
