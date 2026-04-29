from langchain_core.messages import HumanMessage, SystemMessage

from .llm import get_llm
from .state import AgentState


def route(state: AgentState) -> AgentState:
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
