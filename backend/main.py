"""FastAPI app. Usage: uvicorn main:app --reload --port 8000"""
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv(Path(__file__).parent / ".env")

from agent.graph import build_graph
from api.routes import router

DB_PATH = str(Path(__file__).parent / "checkpoints.sqlite")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        app.state.graph = build_graph(checkpointer)
        yield


limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

app = FastAPI(title="op-companion API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


app.add_middleware(SlowAPIMiddleware)
app.include_router(router, prefix="/api")
