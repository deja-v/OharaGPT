"""
Vector store query interface used by the agent's retrieve node.
"""

from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
COLLECTION_NAME = "op_wiki"
EMBED_MODEL = "all-MiniLM-L6-v2"

_collection = None

# Maps known in-universe aliases to their canonical names.
# Used by expand_query() to improve embedding recall.
# Add new aliases here as needed — no other code changes required.
ALIAS_MAP = {
    "gomu gomu no mi": "Hito Hito no Mi, Model: Nika",
    "gomu gomu": "Hito Hito no Mi, Model: Nika",
}


def expand_query(query: str) -> str:
    """
    Appends canonical names for any aliases found in the query.
    Works for any phrasing — substring match on lowercased query.
    Example:
      "What is Gomu Gomu no Mi's real name?"
      → "What is Gomu Gomu no Mi's real name? (Hito Hito no Mi, Model: Nika)"
    """
    q_lower = query.lower()
    expansions = []
    for alias, canonical in ALIAS_MAP.items():
        if alias in q_lower:
            expansions.append(canonical)
    if not expansions:
        return query
    return query + " (" + "; ".join(expansions) + ")"


def diversify(chunks: list[dict], k: int) -> list[dict]:
    """
    Returns up to k chunks, preferring source diversity.
    First pass: take the highest-ranked chunk from each unique source.
    Second pass: fill remaining slots with next-best from any source.
    No page names or sources are hardcoded.
    """
    seen_sources = set()
    result = []

    # First pass — one chunk per source (highest ranked = earliest in list)
    for chunk in chunks:
        if chunk["source"] not in seen_sources:
            seen_sources.add(chunk["source"])
            result.append(chunk)
        if len(result) == k:
            return result

    # Second pass — fill remaining slots
    for chunk in chunks:
        if chunk not in result:
            result.append(chunk)
        if len(result) == k:
            break

    return result


def _get_collection():
    global _collection
    if _collection is None:
        if not INDEX_DIR.exists():
            raise FileNotFoundError(
                f"Vector index not found at {INDEX_DIR}. "
                "Run `python -m rag.index` first."
            )
        embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
        client = chromadb.PersistentClient(path=str(INDEX_DIR))
        _collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn,
        )
    return _collection


def retrieve(query: str, k: int = 6) -> list[dict]:
    """
    Return the top-k wiki chunks most relevant to `query`.

    Each result dict contains:
      - text:    the chunk content
      - source:  filename stem of the wiki page (e.g. "luffy")
      - heading: section heading within the page
      - score:   cosine distance (lower = more similar)
    """
    expanded = expand_query(query)

    collection = _get_collection()
    raw = collection.query(
        query_texts=[expanded],
        n_results=k * 3,  # higher recall gives diversify() more to work with
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    distances = raw["distances"][0]

    for doc, meta, dist in zip(docs, metas, distances):
        chunks.append({
            "text": doc,
            "source": meta.get("source", ""),
            "heading": meta.get("heading", ""),
            "score": round(dist, 4),
        })

    return diversify(chunks, k=k)
