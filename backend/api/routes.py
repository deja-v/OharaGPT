import json
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.graph import build_graph
from api.schemas import ChatRequest, ChatResponse, SourceItem

router = APIRouter()


def _get_checkpointer():
    db_path = str(Path(__file__).parent.parent / "checkpoints.sqlite")
    return SqliteSaver.from_conn_string(db_path)


def _extract_sources(context):
    return [
        SourceItem(source=c["source"], heading=c["heading"], score=c["score"])
        for c in (context or [])
    ]


@router.get("/health")
async def health():
    return {"status": "ok", "service": "op-companion"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    with _get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)
        state = graph.invoke({"question": req.question}, config)
    return ChatResponse(
        answer=state.get("answer", ""),
        sources=_extract_sources(state.get("context")),
        mode=state.get("mode", "qa"),
        verdict=state.get("verdict"),
        thread_id=thread_id,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def generate() -> AsyncGenerator[str, None]:
        with _get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer)
            async for event in graph.astream_events(
                {"question": req.question}, config, version="v1"
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
            state = graph.invoke({"question": req.question}, config)
            done = {
                "type": "done",
                "sources": [s.model_dump() for s in _extract_sources(state.get("context"))],
                "mode": state.get("mode", "qa"),
                "verdict": state.get("verdict"),
                "thread_id": thread_id,
            }
            yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
