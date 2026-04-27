"""
LangGraph agent for answering One Piece questions.

Phase 1: route → answer → END (LLM knowledge only, no RAG).
Phase 2 will insert a `retrieve` node between route and answer.
"""

import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    question: str
    answer: str


# ---------------------------------------------------------------------------
# LLM provider — auto-selects based on available env vars
# ---------------------------------------------------------------------------

def get_llm():
    if os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="gpt-4o-mini",
        base_url="https://models.inference.ai.azure.com",
        api_key=os.getenv("GITHUB_TOKEN"),
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def route(state: AgentState) -> AgentState:
    """
    Passthrough in Phase 1.
    Phase 2 will use this node to decide whether retrieval is needed.
    """
    return state


def answer(state: AgentState) -> AgentState:
    llm = get_llm()
    messages = [
        SystemMessage(content=(
            "You are an expert on the One Piece manga and anime. "
            "Answer questions accurately and concisely. "
            "If you're not certain about something, say so."
        )),
        HumanMessage(content=state["question"]),
    ]
    response = llm.invoke(messages)
    return {"question": state["question"], "answer": response.content}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph(checkpointer):
    graph = StateGraph(AgentState)

    graph.add_node("route", route)
    graph.add_node("answer", answer)

    graph.set_entry_point("route")
    graph.add_edge("route", "answer")
    graph.add_edge("answer", END)

    return graph.compile(checkpointer=checkpointer)
