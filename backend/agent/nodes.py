import re

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


THEORY_TRIGGERS = [
    "is it possible",
    "could it be",
    "do you think",
    "theory:",
    "theory about",
    "is the theory",
    "do you believe",
    "what if",
    "might be",
    "could be related",
    "is secretly",
    "actually a",
    "is actually",
    "could luffy",
    "could zoro",
    "is imu",
]

VERDICT_CHUNK_MAX_CHARS = 800
VERDICT_MAX_CHUNKS_PER_SUB = 2


def classify_mode(state: AgentState) -> AgentState:
    q = state["question"].lower()
    mode = "theory" if any(trigger in q for trigger in THEORY_TRIGGERS) else "qa"
    return {"mode": mode}


def _parse_sub_questions(text: str) -> list[str]:
    result = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        if line:
            result.append(line)
        if len(result) >= 4:
            break
    return result


def decompose_theory(state: AgentState) -> AgentState:
    system_prompt = (
        "You are analyzing a One Piece theory. Break it into 2-4 concrete sub-questions "
        "that can each be independently verified using the One Piece wiki.\n\n"
        "Rules:\n"
        "- Each sub-question must be factual and specific (not opinion-based)\n"
        "- Sub-questions should cover: what is confirmed, what contradicts, what is unknown\n"
        "- Format: numbered list, one sub-question per line, no extra text\n\n"
        f"Theory: {state['question']}\n\n"
        "Output format:\n"
        "1. [sub-question]\n"
        "2. [sub-question]\n"
        "3. [sub-question]"
    )
    llm = get_llm()
    response = llm.invoke([SystemMessage(content=system_prompt)])
    sub_questions = _parse_sub_questions(response.content)
    return {"sub_questions": sub_questions}


def evidence_hunt(state: AgentState) -> AgentState:
    all_evidence = []
    for sub_q in state.get("sub_questions", []):
        for chunk in retrieve(sub_q, k=3):
            all_evidence.append({
                "sub_question": sub_q,
                "text": chunk["text"],
                "source": chunk["source"],
                "heading": chunk["heading"],
                "score": chunk["score"],
            })
    return {"evidence": all_evidence}


def _extract_verdict(text: str) -> str:
    upper = text.upper()
    if "SUPPORTED" in upper:
        return "SUPPORTED"
    if "CONTRADICTED" in upper:
        return "CONTRADICTED"
    return "INSUFFICIENT"


def synthesize_verdict(state: AgentState) -> AgentState:
    evidence = state.get("evidence") or []
    by_sub: dict[str, list[dict]] = {}
    for item in evidence:
        sub_q = item["sub_question"]
        by_sub.setdefault(sub_q, []).append(item)

    blocks = []
    for sub_q, chunks in by_sub.items():
        selected = chunks[:VERDICT_MAX_CHUNKS_PER_SUB]
        chunk_text = "\n\n".join(
            f"[Source: {c['source']} — {c['heading']}]\n{c['text'][:VERDICT_CHUNK_MAX_CHARS]}"
            for c in selected
        )
        blocks.append(f"Sub-question: {sub_q}\n{chunk_text}")

    context_block = "\n\n---\n\n".join(blocks) if blocks else "(no evidence retrieved)"

    system_prompt = (
        "You are verifying a One Piece fan theory using wiki excerpts only.\n\n"
        "Verdict definitions:\n"
        "- SUPPORTED — wiki explicitly confirms a key element of the theory\n"
        "- CONTRADICTED — wiki explicitly contradicts a key element\n"
        "- INSUFFICIENT — not enough confirmed evidence to decide (speculation, unconfirmed)\n\n"
        "GROUNDING RULES:\n"
        "1. Base your verdict only on the excerpts below.\n"
        "2. Cite sources for every fact, e.g. (Source: bonney — Background).\n"
        "3. If excerpts lack enough information, use INSUFFICIENT.\n\n"
        "Output format (required):\n"
        "Verdict: SUPPORTED | CONTRADICTED | INSUFFICIENT\n\n"
        "[2-3 sentence explanation with citations]\n\n"
        "Supporting evidence: (Source: ...), (Source: ...)\n\n"
        f"Theory: {state['question']}\n\n"
        f"Wiki excerpts by sub-question:\n{context_block}"
    )

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["question"]),
    ])
    answer_text = response.content
    verdict = _extract_verdict(answer_text)
    return {"verdict": verdict, "answer": answer_text}
