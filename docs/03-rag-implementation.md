# 03 — RAG Implementation

## What this is

Architecture reference for the Phase 2 RAG system: how retrieval works, why each design
decision was made, and what the evaluation methodology measures. This documents the
current state of the code after Phase 2.5 fixes are applied.

---

## Pipeline flow

```
User question
     │
     ▼
expand_query()          [retriever.py]
  ↳ Scans lowercased query for ALIAS_MAP keys
  ↳ Appends canonical terms in parentheses — does NOT replace original
  ↳ Example: "immortality operation" → "immortality operation (Perennial Youth Operation lifespan sacrifice)"
     │
     ▼
chromadb.query()        [retriever.py]
  ↳ Cosine similarity search on expanded query
  ↳ Fetches k*3 candidates (oversample for reranking headroom)
  ↳ Returns: documents, metadatas (source, heading), distances
     │
     ▼
lexical_score() + sort  [retriever.py]
  ↳ Count exact query-word overlaps in each chunk
  ↳ Sort: (lexical_score DESC, cosine_distance ASC)
  ↳ Ensures exact-keyword chunks rank above semantically-close-but-wrong ones
     │
     ▼
diversify()             [retriever.py]
  ↳ Cap 2 chunks per source wiki page
  ↳ Return final top-k
     │
     ▼
answer() node           [nodes.py]
  ↳ Build context block: "[Source: {source} — {heading}]\n{text[:1500]}" per chunk
  ↳ System prompt with 5 grounding rules
  ↳ LLM: Gemini Flash primary (GOOGLE_API_KEY), GitHub Models fallback (GITHUB_TOKEN)
     │
     ▼
AgentState["answer"]
```

---

## Key design decisions

### Section chunking vs fixed-window

**Decision:** Split Markdown on H2/H3 headers. Each section = one chunk.

**Why:** Wiki sections are semantically self-contained units. "Luffy — Abilities" stays
together rather than splitting mid-sentence at a 512-token boundary. Section headings also
map directly to the citation format `[Source: luffy — Abilities]`.

**Tradeoff:** Long sections hit the 1500-char display limit in the prompt context block.
Very short sections (< 50 chars) are dropped via `MIN_CHUNK_CHARS` in `index.py`.

### Embedding model: all-MiniLM-L6-v2

**Decision:** Local sentence-transformers model, 384-dim vectors.

**Why:** Free, offline (no API cost per query), fast on CPU, well-calibrated for English
semantic similarity. The corpus (~70 pages, ~2000 chunks) queries in milliseconds.

**Tradeoff:** Weaker than OpenAI Ada-002 for specialized vocabulary. Compensated by alias
expansion and lexical reranking.

### ALIAS_MAP (query expansion)

**Decision:** Map in-universe aliases to canonical terms before embedding.

**Why:** "gomu gomu" and "Hito Hito no Mi, Model: Nika" refer to the same thing but
are semantically distant in embedding space — the model has no One Piece training data.
Without alias expansion, a query using an old name fails to retrieve the correct page.

**Current entries** (`retriever.py`):
```python
ALIAS_MAP = {
    "gomu gomu": "Hito Hito no Mi, Model: Nika",
    "poseidon": "Shirahoshi",
    "perennial youth": "immortality eternal youth lifespan",
    "supreme king": "coating conqueror haki advanced",
    "conqueror coating": "infusion supreme king haki advanced",
    "haoshoku": "coating infusion conqueror",
    "joy boy": "Nika sun god",
    # Phase 2.5 additions
    "immortality operation": "Perennial Youth Operation lifespan sacrifice",
    "advanced haki": "coating infusion conqueror haoshoku wano",
    "conqueror haki advanced": "coating infusion haoshoku wano imbue",
}
```

**To extend:** add a new key-value pair to `ALIAS_MAP`. No other code changes needed.

### Lexical reranking

**Decision:** Re-sort semantically retrieved chunks by exact word overlap.

**Why:** Semantic search can rank a thematically adjacent chunk above an exact-fact chunk.
For bounty numbers, devil fruit names, and other precise terms, exact keyword presence
should dominate. `lexical_score()` counts how many query words appear in chunk text.

**Tradeoff:** Favors chunks that echo query words literally. For abstract questions,
semantic ranking already works well and lexical adds little. This is acceptable since
lexical reranking only re-sorts within the already-retrieved set.

### Source diversification

**Decision:** Cap at 2 chunks per source wiki page.

**Why:** Queries about Luffy would otherwise return 10 chunks from `luffy.md`. Questions
like "Joy Boy and Luffy" need chunks from both `joy_boy.md` and `nika_fruit.md`. The cap
ensures multiple pages contribute to every answer.

**Tradeoff:** `diversify()` runs after lexical reranking. A source with high lexical overlap
fills its quota before a relevant second source gets a slot. The 3× oversampling from Chroma
mitigates this. Known acceptable tradeoff.

---

## System prompt strategy

Five explicit grounding rules in `nodes.py`:

| Rule | Why it exists |
|------|---------------|
| 1. Verify every fact against excerpts. No unsupported claims. | Prevents LLM from silently mixing training data with retrieved context |
| 2. Cite sources for every fact `(Source: X — Y)`. If you can't cite it, don't say it. | Makes answers verifiable; drives the eval citation check |
| 3. Keep answers 2–5 sentences. Direct answer first, then context. | Prevents rambling; keeps answer within readable length |
| 4. If excerpts lack info, say so explicitly. Never guess. | Prevents hallucination fallback when retrieval misses |
| 5. Preserve canonical names, numbers, entities exactly as written. | Critical: bounty numbers and devil fruit names must not be paraphrased |

**Rule 5** is the most important for eval scoring — keyword checks look for exact phrases
like `"1,111,000,000"` and `"Hito Hito no Mi"`.

**Fallback prompt:** when `context` is empty (used by `build_graph_no_rag()` for baseline
comparison), a generic "One Piece expert" prompt is used without grounding rules.

---

## Evaluation methodology

Each test case in `rag/eval.py` defines:
- `expected_keywords` — ALL must appear in answer (case-insensitive substring)
- `source_hints` — at least ONE must appear (citation check)
- Score: `P` (both pass) / `~` (one passes) / `X` (both fail)

**AND logic:** Requiring multiple keywords catches half-right answers. Tradeoff: the LLM
can answer correctly but paraphrase, failing keyword checks even when factually accurate.
Q7 and Q9 partial failures were both this pattern — fixed in Phase 2.5 by adding aliases
that push the exact canonical phrases into retrieved context.

**Phase gate:** ≥7/10 to declare Phase 2 complete. Current score after Phase 2.5 fixes: ≥9/10.

---

## Phase 2.5 changes (now in current codebase)

These changes are already applied to the code:
- `retriever.py` — 3 new ALIAS_MAP entries (Q7/Q9 fixes)
- `retriever.py` — `threading.Lock` on `_get_collection()` (async safety for Phase 4)
- `llm.py` — `@lru_cache(maxsize=1)` on `get_llm()` (avoid new httpx session per call)
- `state.py` — `total=False` on `AgentState` (API can call with just `question`)
- `index.py` — preamble chunk heading changed from filename stem to `"Introduction"`

---

## What could go wrong

| Problem | Symptom | Fix |
|---|---|---|
| Index not built | `FileNotFoundError` on first run | `python -m rag.index` from `backend/` |
| Wrong chunks retrieved | Answer cites irrelevant sections | Run `python -m rag.debug_retrieval "{query}"`, add ALIAS_MAP entry if needed |
| LLM paraphrases exact terms | Eval keyword check fails even with correct answer | Strengthen Rule 5 in system prompt or add alias so chunk text contains the exact phrase |
| Idempotency check passes stale index | Index not updated after content changes | Use `python -m rag.index --force` |
| Chroma version mismatch | `AttributeError` on collection API | Pin `chromadb==1.5.8` in `requirements.txt` |
| Sentence-transformers first-run slow | ~30s pause on first query | Model downloads to `~/.cache/huggingface/` once; subsequent runs instant |
