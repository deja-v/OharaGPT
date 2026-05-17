# 02 — RAG Pipeline

## What this is

A three-stage pipeline that gives the agent access to factual wiki content:

1. **Scrape** — download ~70 One Piece wiki pages as Markdown files
2. **Index** — chunk and embed them into a local Chroma vector store
3. **Retrieve** — at query time, pull the 6 most relevant chunks and inject them into the LLM prompt

The agent graph becomes `route → retrieve → answer → END`. Every fact in the answer must cite which wiki page it came from.

---

## Why RAG is needed here

The LLM knows broad One Piece lore but hallucinates specifics:
- Exact bounty values (e.g. Dorry: 100,000,000 Berries)
- Devil fruit true names (Gomu Gomu no Mi vs. Hito Hito no Mi, Model: Nika)
- Recent Final Saga reveals (Joy Boy / Nika connection, Five Elders' devil fruits)
- Void Century confirmed facts vs. fan speculation

Without retrieval, the model guesses. With retrieval, every answer is grounded in the actual wiki text, and the citation tells you exactly where the fact comes from.

---

## Scraper (`rag/scrape.py`)

**Politeness budget:** 1 request per second, `User-Agent` header identifies the bot.

**Page selection:** ~70 hand-curated pages across six categories:
- Straw Hat crew + key allies/mentors
- Emperors (Yonko) + main antagonists
- World Government / Celestial Dragons
- Devil Fruits (by type + key individual fruits)
- Haki
- Lore (Poneglyphs, Void Century, Will of D., Bounty, Grand Line, major arcs)

**HTML → Markdown:** `beautifulsoup4` strips navigation and reference noise; `markdownify` converts the body to ATX-style Markdown. The page title is prepended as an H1 so every chunk carries its origin.

**Infobox preservation:** Fandom wiki infoboxes (`<aside class="portable-infobox">`) contain structured key-value data (bounties, devil fruits, affiliations). Before the `<aside>` is stripped, the scraper extracts every `pi-data-label` / `pi-data-value` pair and writes them as a `## Infobox` section at the top of the page. This ensures numeric facts like bounty amounts survive into the vector index.

**Idempotency:** files in `backend/data/raw/` are never re-fetched unless deleted. Re-running the script only fetches missing pages.

**Output:** `backend/data/raw/<stem>.md` — one file per page.

---

## Chunking strategy (`rag/index.py`)

Chunks are split at **H2/H3 section boundaries**, not at fixed character counts.

**Why section-based over fixed-size:**
- Wiki pages are already organized into meaningful sections (History, Abilities, Relationships, etc.)
- A fixed 500-character chunk often splits mid-sentence or mid-topic
- Section chunks preserve the context needed to answer questions about a specific aspect of a character

**Minimum chunk size:** 100 characters — filters out stub sections with no real content.

**Chunk metadata stored alongside each embedding:**
- `source`: filename stem (e.g. `"luffy"`) — used as the wiki page reference in citations
- `heading`: the H2/H3 section title

---

## Alias injections (`rag/index.py`)

Some facts are hidden behind aliases or partial names (e.g. "Gomu Gomu no Mi" vs. its true name "Hito Hito no Mi, Model: Nika"). Semantic search alone may retrieve the wrong page.

To guide retrieval, `index.py` prepends **alias injection notes** to specific pages before chunking:

```python
ALIAS_INJECTIONS = {
    "nika_fruit": "Note: This page covers the Hito Hito no Mi Model Nika, ...",
    "gomu_gomu": "Note: Gomu Gomu no Mi is an ALIAS. The official true name is ...",
    "joy_boy": "Note: Joy Boy is connected to the Sun God Nika and Monkey D. Luffy...",
}
```

These notes embed cross-reference hints directly into the vector store so embeddings connect aliases to the canonical page.

---

## Embedding model

**Model:** `all-MiniLM-L6-v2` (via `sentence-transformers`)

**Why this model:**
- Free, local, offline — no API calls, no cost
- 80 MB download, runs on CPU in milliseconds per query
- 384-dimension embeddings; good semantic accuracy for English prose
- Directly supported by Chroma's `SentenceTransformerEmbeddingFunction`

**Alternatives considered:**
- OpenAI `text-embedding-3-small`: better quality but costs money and requires internet
- `all-mpnet-base-v2`: higher quality, but 3× the inference time — unnecessary for ~70 pages

---

## Vector store

**Choice:** `chromadb` with `PersistentClient`

**Why Chroma over `sqlite-vss`:**
- `sqlite-vss` requires a compiled C extension that is unreliable on Windows without WSL
- Chroma is pure Python install, zero server setup, and officially supported
- Single directory at `backend/data/index/` — portable with the repo

**Distance metric:** cosine similarity (`hnsw:space: cosine`)

**Index persistence:** the Chroma collection survives between runs. `index.py` is idempotent — it skips re-indexing if the chunk count matches. Pass `--force` to rebuild from scratch.

---

## Retrieval (`rag/retriever.py`)

**Interface:** `retrieve(query: str, k: int = 6) → list[dict]`

Each result contains: `text`, `source`, `heading`, `score` (cosine distance, lower = better).

**k=6:** six chunks gives the LLM enough context while fitting the prompt budget. A typical chunk is 300–800 characters, so 6 chunks ≈ 2,000–4,000 tokens of context.

**Keyword-based source boost:** for known tricky queries (e.g. "official name of Luffy's devil fruit"), `KEYWORD_SOURCE_BOOST` maps keyword tuples to source stems that **must** be included. After the normal Chroma query, any boosted source not already in results is fetched separately via a filtered query and appended. This ensures the canonical page (e.g. `nika_fruit`) is never absent even if the embedding ranks a different page higher.

**Lazy loading:** the Chroma collection is loaded once on first call and cached in a module-level variable. Subsequent calls within the same process reuse the connection.

---

## Prompt injection and citations

When the `retrieve` node returns chunks, the `answer` node builds a system prompt that:
1. Provides each chunk with its `[Source: <stem> — <heading>]` label
2. Prepend a **CRITICAL INSTRUCTION** block telling the LLM its training knowledge is outdated and it must prefer retrieved evidence (especially for known override scenarios like Luffy's devil fruit name)
3. Instructs the LLM to cite sources for every fact
4. Instructs the LLM to explicitly say when the excerpts don't contain enough information (rather than guessing)

When no chunks are available (empty context), the agent falls back to LLM-only answering with a note about uncertainty.

---

## What could go wrong

| Problem | Symptom | Fix |
|---|---|---|
| Wiki page slug is wrong | HTTP 404 in scrape output | Check the exact URL on onepiece.fandom.com and update `PAGES` in `scrape.py` |
| Index not built | `FileNotFoundError` on first agent run | Run `python -m rag.index` from `backend/` |
| Wrong chunks retrieved | Answer cites irrelevant sections | Increase `k`, improve query, add `KEYWORD_SOURCE_BOOST` entries in `retriever.py` |
| LLM overrides retrieval with training knowledge | Answer uses training data instead of wiki excerpts | Strengthen the system prompt's override instructions in `nodes.py` |
| Alias injection missing | Correct page not retrieved for alias-based queries | Add entry to `ALIAS_INJECTIONS` in `index.py` and re-index |
| Chroma version mismatch | `AttributeError` on collection API | Pin `chromadb==1.5.8` in `requirements.txt` |
| Sentence-transformers first run slow | ~30s pause on first query | Model downloads to `~/.cache/huggingface/` on first use; subsequent runs are instant |

---

## Where to read more

- [Chroma docs](https://docs.trychroma.com/)
- [sentence-transformers model hub](https://www.sbert.net/docs/pretrained_models.html)
- [all-MiniLM-L6-v2 on HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [One Piece Wiki](https://onepiece.fandom.com/wiki/)
