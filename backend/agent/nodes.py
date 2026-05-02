from langchain_core.messages import HumanMessage, SystemMessage

from rag.retriever import retrieve
from .llm import get_llm
from .state import AgentState


def route(state: AgentState) -> AgentState:
    return state


def retrieve_node(state: AgentState) -> AgentState:
    chunks = retrieve(state["question"], k=4)
    return {"question": state["question"], "context": chunks, "answer": ""}


def answer(state: AgentState) -> AgentState:
    context = state.get("context") or []

    if context:
        context_block = "\n\n".join(
            f"[Source: {c['source']} — {c['heading']}]\n{c['text']}"
            for c in context
        )
        system_prompt = (
            "You are an expert on the One Piece manga and anime. "
            "Answer questions using ONLY the wiki excerpts provided below. "
            "For every fact you state, cite the source in parentheses, "
            "e.g. (Source: luffy — Abilities). "
            "If the excerpts do not contain enough information to answer, say so explicitly.\n\n"
            f"Wiki excerpts:\n{context_block}"
        )
    else:
        system_prompt = (
            "You are an expert on the One Piece manga and anime. "
            "Answer questions accurately and concisely. "
            "If you're not certain about something, say so."
        )

    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["question"]),
    ]
    response = llm.invoke(messages)
    return {"question": state["question"], "context": context, "answer": response.content}
