from langchain_core.messages import HumanMessage, SystemMessage

from rag.retriever import retrieve
from .llm import get_llm
from .state import AgentState

CHUNK_MAX_CHARS=1500


def retrieve_node(state: AgentState) -> AgentState:
    return {"context": retrieve(state["question"])}


def answer(state: AgentState) -> AgentState:
    context = state.get("context") or []

    if context:
        context_block = "\n\n".join(
            f"[Source: {c['source']} — {c['heading']}]\n{c['text'][:CHUNK_MAX_CHARS]}"
            for c in context
        )
        system_prompt = (
            "You are a RAG-grounded assistant. "
            "The excerpts below are your ONLY source of truth. "
            "Your training knowledge is OUTDATED. "
            "When excerpts contain an answer, use it — even if it contradicts "
            "what you know from training.\n\n"
            "GROUNDING RULES:\n"
            "1. Verify each fact against the excerpts. "
            "Do not include unsupported claims.\n"
            "2. Cite sources for every fact, "
            "e.g. (Source: luffy — Abilities). "
            "If you cannot cite it, do not assert it.\n"
            "3. Keep answers concise (2-5 sentences). "
            "Answer directly, then add brief context from excerpts.\n"
            "4. If the excerpts lack enough information to answer clearly, "
            "say so explicitly. Do not guess or use training knowledge.\n"
            "5. Preserve canonical names, numbers, and entities "
            "exactly as they appear in the excerpts.\n\n"
            f"Wiki excerpts:\n{context_block}"
        )
    else:
        system_prompt = (
            "You are an expert on the One Piece manga and anime. "
            "Answer questions accurately and concisely. "
            "If you are uncertain about something, say so."
        )

    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["question"]),
    ]
    response = llm.invoke(messages)
    return {"answer": response.content}
