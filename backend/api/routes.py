import json
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.graph import build_graph
from api.schemas import ChatRequest, ChatResponse, SourceItem

router = APIRouter()
DB_PATH = str(Path(__file__).parent.parent / "checkpoints.sqlite")


def _extract_sources(chunks):
    return [
        SourceItem(source=c["source"], heading=c.get("heading", ""), score=c.get("score", 0.0))
        for c in (chunks or [])
    ]


@router.get("/health")
async def health():
    return {"status": "ok", "service": "op-companion"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    try:
        graph = request.app.state.graph
        state = graph.invoke({"question": req.question}, config)
        src = _extract_sources(state.get("context") or state.get("evidence"))
        return ChatResponse(
            answer=state.get("answer", ""),
            sources=src,
            mode=state.get("mode", "qa"),
            verdict=state.get("verdict"),
            thread_id=thread_id,
        )
    except Exception:
        return ChatResponse(
            answer="Request failed. Please try again.",
            sources=[],
            mode="qa",
            verdict=None,
            thread_id=thread_id,
        )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def generate() -> AsyncGenerator[str, None]:
        try:
            async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
                graph = build_graph(checkpointer)
                async for event in graph.astream_events(
                    {"question": req.question}, config, version="v1"
                ):
                    if event["event"] == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            yield f"event: token\ndata: {json.dumps({'content': chunk.content})}\n\n"
                state_snapshot = await graph.aget_state(config)
                state = state_snapshot.values if state_snapshot else {}
                src = _extract_sources(state.get("context") or state.get("evidence"))
                yield (
                    f"event: done\n"
                    f"data: {json.dumps({'sources': [s.model_dump() for s in src], 'mode': state.get('mode', 'qa'), 'verdict': state.get('verdict'), 'thread_id': thread_id})}\n\n"
                )
        except Exception:
            yield f"event: error\ndata: {json.dumps({'error': 'Stream failed'})}\n\n"
            yield f"event: done\ndata: {json.dumps({'sources': [], 'mode': 'qa', 'verdict': None, 'thread_id': thread_id})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
