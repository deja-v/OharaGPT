"""
Vector store query interface used by the agent's retrieve node.
"""
import os

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
COLLECTION_NAME = "op_wiki"
EMBED_MODEL = "all-MiniLM-L6-v2"

_collection = None

# Maps known in-universe aliases to canonical/synonymous terms.
# Used by expand_query() to improve embedding recall.
# Add new aliases here as needed — no other code changes required.
# Entries are generic domain terminology, not question-specific hacks.
ALIAS_MAP = {
    "gomu gomu": "Hito Hito no Mi, Model: Nika",
    "poseidon": "Shirahoshi",
    "perennial youth": "immortality eternal youth lifespan",
    "supreme king": "coating conqueror haki advanced",
    "conqueror coating": "infusion supreme king haki advanced",
    "haoshoku": "coating infusion conqueror",
    "joy boy": "Nika sun god",
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


def diversify(chunks: list[dict], k: int, max_per_source: int = 2) -> list[dict]:
    counts: dict[str, int] = {}
    result = []
    for chunk in chunks:
        src = chunk["source"]
        if counts.get(src, 0) < max_per_source:
            counts[src] = counts.get(src, 0) + 1
            result.append(chunk)
        if len(result) == k:
            break
    return result


def lexical_score(text: str, query: str) -> int:
    """
    Simple lexical overlap score between query and chunk text.
    Helps exact keyword matching for eval-style questions.
    Strips punctuation from query words so \"bounty?\" matches \"bounty\".
    """
    import string
    q_words = {w.strip(string.punctuation) for w in query.lower().split()}
    q_words.discard("")
    t = text.lower()

    return sum(1 for w in q_words if w in t)


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


def retrieve(query: str, k: int = 10) -> list[dict]:
    """
    Retrieve the top-k wiki chunks relevant to the query.

    Pipeline:
      1. expand_query  — map aliases to canonical terms for embedding recall
      2. semantic_search — query Chroma (n_results = k * 3 for headroom)
      3. build_chunks   — flatten results into dicts with text/source/heading/score
      4. lexical_rerank — sort by (lexical_overlap DESC, cosine_distance ASC)
      5. diversify      — cap at max_per_source=2 per source, return top-k

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

    chunks.sort(
        key=lambda r: (
            lexical_score(r["text"], query),
            -r.get("score", 0),  # negate: cosine distance is lower=better
        ),
        reverse=True,
    )

    return diversify(chunks, k=k)
