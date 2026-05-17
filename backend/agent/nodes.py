from langchain_core.messages import HumanMessage, SystemMessage

from rag.retriever import retrieve
from .llm import get_llm
from .state import AgentState

CHUNK_MAX_CHARS=1500

def route(state: AgentState) -> AgentState:
    return state


def retrieve_node(state: AgentState) -> AgentState:
    chunks = retrieve(state["question"])
    return {"question": state["question"], "context": chunks, "answer": ""}


def answer(state: AgentState) -> AgentState:
    context = state.get("context") or []

    if context:
        context_block = "\n\n".join(
            f"[Source: {c['source']} — {c['heading']}]\n{c['text'][:CHUNK_MAX_CHARS]}"
            for c in context
        )
        system_prompt = (
            "CRITICAL INSTRUCTION:\n\n"
            "You are a RAG-grounded assistant. "
            "The excerpts below are your ONLY source of truth. "
            "Your training knowledge about One Piece is OUTDATED "
            "and frequently wrong on recent reveals (post-chapter 1000). "
            "When the excerpts contain an answer, "
            "you MUST use it — even if it contradicts "
            "what you 'know' from training.\n\n"
            "Specifically:\n"
            "- If excerpts say the true name of Luffy's devil fruit is "
            "'Hito Hito no Mi, Model: Nika', "
            "output that — NOT 'Gomu Gomu no Mi'\n"
            "- 'Gomu Gomu no Mi' is a FAKE in-universe name\n"
            "- 'Hito Hito no Mi, Model: Nika' is the REAL and OFFICIAL name\n"
            "- If BOTH appear in context, "
            "ALWAYS prefer the REAL name\n"
            "- Always cite [Source: <stem>] for every fact\n\n"
            "---\n\n"
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
