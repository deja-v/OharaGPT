# 05 — API Layer (Phase 4)

## What this is

A [FastAPI](https://fastapi.tiangolo.com/) HTTP server wrapping the LangGraph agent. Phase 5 (React frontend) calls these endpoints from `localhost:5173`.

**Entry point:** `backend/main.py` — run with uvicorn, not `python main.py`.

---

## Running the server

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check: `http://localhost:8000/api/health` → `{"status": "ok", "service": "op-companion"}`.

**CLI (unchanged behavior, different file):**

```bash
cd backend
python cli.py "What is Zoro's bounty?"
```

---

## Endpoints

All routes are under prefix `/api`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/chat` | Full graph invoke, JSON response |
| `POST` | `/chat/stream` | SSE token stream + final `done` event |

**Rate limit:** 30 requests/minute per IP (SlowAPI).

**CORS:** `http://localhost:5173`, `http://localhost:3000`.

---

## POST /chat

**Request:**

```json
{
  "question": "What is Zoro's bounty after Wano?",
  "thread_id": "optional-uuid"
}
```

If `thread_id` is omitted, the server generates a new `uuid4()`.

**Response:**

```json
{
  "answer": "Roronoa Zoro's bounty...",
  "sources": [
    {"source": "zoro", "heading": "Bounty", "score": 0.12}
  ],
  "mode": "qa",
  "verdict": null,
  "thread_id": "abc123"
}
```

| Field | QA path | Theory path |
|-------|---------|-------------|
| `mode` | `"qa"` | `"theory"` |
| `verdict` | `null` | `SUPPORTED`, `CONTRADICTED`, or `INSUFFICIENT` |
| `sources` | From `context` chunks | Usually `[]` (evidence not mapped to sources yet) |

---

## POST /chat/stream

Same request body. Returns `text/event-stream`:

```
data: {"type": "token", "content": "Roronoa"}

data: {"type": "token", "content": " Zoro"}

data: {"type": "done", "sources": [...], "mode": "qa", "verdict": null, "thread_id": "abc123"}
```

**Phase 4 shortcut:** Streaming uses `astream_events` for tokens, then a second `graph.invoke` for final metadata (`sources`, `mode`, `verdict`). Phase 5 may consolidate to a single run.

---

## File structure

```
backend/
├── main.py           # FastAPI app (uvicorn entry)
├── cli.py            # CLI invoke (Phase 1–3 style)
├── api/
│   ├── schemas.py    # Pydantic request/response models
│   └── routes.py     # Router: health, chat, chat/stream
└── evals/
    └── api_eval.py   # HTTP gate (10 questions)
```

---

## Evaluation gate

Server must be running on port 8000:

```bash
# Terminal 1
uvicorn main:app --port 8000

# Terminal 2
cd backend
python -m evals.api_eval
```

**Pass criteria:** 10/10 HTTP 200 responses and ≥8/10 keyword matches (reuses `rag.eval` scoring).

---

## Troubleshooting

| Problem | Symptom | Fix |
|---------|---------|-----|
| Server unreachable | `api_eval` exits on health check | Start uvicorn from `backend/` |
| 429 Too Many Requests | Rate limit exceeded | Wait 60s or reduce request rate |
| CORS error in browser | Blocked from Vite | Confirm origin is `localhost:5173` |
| Empty `sources` on theory | Expected in Phase 4 | Theory uses `evidence`, not `context` |
| Index not built | 500 / FileNotFoundError in logs | `python -m rag.index` |

---

## Related docs

- [01 — Agent Graph](./01-agent-graph.md) — LangGraph, checkpoints
- [04 — Theory Verification](./04-theory-verification.md) — `mode` and `verdict`
- Plan: `plans/op-companion-phase-4-api.md`
- Next: `plans/op-companion-phase-5-frontend.md`
