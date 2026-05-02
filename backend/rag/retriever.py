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


def retrieve(query: str, k: int = 4) -> list[dict]:
    """
    Return the top-k wiki chunks most relevant to `query`.

    Each result dict contains:
      - text:    the chunk content
      - source:  filename stem of the wiki page (e.g. "luffy")
      - heading: section heading within the page
      - score:   cosine distance (lower = more similar)
    """
    collection = _get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(docs, metas, distances):
        chunks.append({
            "text": doc,
            "source": meta.get("source", ""),
            "heading": meta.get("heading", ""),
            "score": round(dist, 4),
        })

    return chunks
