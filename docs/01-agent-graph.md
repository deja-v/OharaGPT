# 01 — Agent Graph

## What this is

A [LangGraph](https://langchain-ai.github.io/langgraph/) `StateGraph` that answers One Piece questions using RAG. It retrieves relevant chunks from a local Chroma vector store (built from the One Piece wiki) and injects them into the LLM prompt as the exclusive source of truth.

LangGraph version targeted: **1.1.9**

---

## The mental model: state machines over state dicts

LangGraph models an agent as a **directed graph** where:

- Each **node** is a Python function that takes the current state and returns an updated state.
- Each **edge** is a transition between nodes (can be conditional or fixed).
- The **state** is a plain `TypedDict` that flows through every node unchanged unless a node explicitly updates a key.

```
user question
     │
     ▼
  [route] ──► [retrieve] ──► [answer] ──► END
  (passthrough)   (query index)   (calls LLM)
```

The graph is compiled once and then called with `.invoke()`. Each invocation runs from the entry point (`route`) to `END`.

---

## State (`AgentState`)

Defined in `backend/agent/state.py`:

```python
class AgentState(TypedDict):
    question: str                     # set by the caller before first node runs
    context: list[dict]               # populated by the `retrieve` node
    answer: str                       # populated by the `answer` node
```

LangGraph passes this dict into each node. A node returns a partial dict — only the keys it changed. LangGraph merges the return value back into the state automatically.

---

## Nodes

Defined in `backend/agent/nodes.py`.

### `route`

Currently a passthrough — returns `state` unchanged. It is the intended decision point for "does this question need retrieval?" — having it in the graph now means adding retrieval is an edit to one function, not a structural change.

### `retrieve`

Calls `rag.retriever.retrieve(state["question"], k=6)` and stores the result in `state["context"]`. Each chunk contains `text`, `source`, `heading`, and `score`.

### `answer`

When context is available, the system prompt is structured as:
1. A **CRITICAL INSTRUCTION** block that tells the LLM its training knowledge is outdated and it must prefer retrieved evidence (with explicit override scenarios like Luffy's devil fruit name)
2. The wiki excerpts with `[Source: <stem> — <heading>]` labels
3. Instructions to cite sources and say when information is insufficient

When context is empty, the agent falls back to LLM-only answering with a note about uncertainty.

Returns `{"answer": response.content}` (LangGraph merges this into the full state).

---

## LLM selection (`get_llm()`)

Defined in `backend/agent/llm.py`. The function checks env vars in priority order:

```
GOOGLE_API_KEY set?  →  Gemini Flash (gemini-2.0-flash)
       │ no
       ▼
GITHUB_TOKEN set?    →  GPT-4o-mini via GitHub Models (OpenAI-compatible endpoint)
```

Both are $0 spend. Swapping providers requires only changing the env var — no graph code changes.

To add your Gemini key later, just set `GOOGLE_API_KEY=<your_key>` in `.env`. The agent switches automatically on next run.

---

## Checkpoints and `SqliteSaver`

LangGraph can persist the full state after every node transition. We use `langgraph-checkpoint-sqlite` (version 3.0.3), which writes to a local SQLite file at `backend/checkpoints.sqlite`.

```python
with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
    graph = build_graph(checkpointer)
    graph.invoke(initial_state, config)
```

The `with` block ensures the connection is closed cleanly after the run.

### What gets written

Every time a node finishes, LangGraph writes a checkpoint row containing:
- The `thread_id` (identifies which conversation the step belongs to)
- The node name that just ran
- The full state dict at that point
- A timestamp and sequence number

### Why `thread_id` matters

`thread_id` is the key that lets LangGraph resume a conversation. If you call `.invoke()` twice with the same `thread_id`, the second call continues from where the first left off (state is reloaded from the DB). In `main.py` we generate a fresh `uuid4()` per CLI run, so each question is an independent conversation.

This is also what makes `langgraph-replay` work: it reads the checkpoint rows grouped by `thread_id` and can replay any run step-by-step.

### Inspecting the DB

Open `backend/checkpoints.sqlite` in DBeaver (or any SQLite browser):
- Table: `checkpoints` — one row per (thread_id, step)
- Table: `writes` — intermediate node output writes

---

## What could go wrong

| Problem | Symptom | Fix |
|---|---|---|
| No env vars set | `GITHUB_TOKEN` or `GOOGLE_API_KEY` missing → auth error | Add the key to `.env` |
| GitHub Models rate limit | HTTP 429 from the API | Wait 60s, or switch to `GOOGLE_API_KEY` |
| LangGraph version drift | `SqliteSaver` API changes | Always use `langgraph-checkpoint-sqlite==3.0.3` from `requirements.txt` |

---

## Where to read more

- [LangGraph conceptual docs](https://langchain-ai.github.io/langgraph/concepts/)
- [SqliteSaver reference](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.SqliteSaver)
- [GitHub Models free tier](https://docs.github.com/en/github-models)
- [Google AI Studio (Gemini free tier)](https://aistudio.google.com)
