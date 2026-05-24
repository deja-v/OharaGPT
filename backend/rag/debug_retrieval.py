"""
Debug retrieval: shows what chunks are returned for a query,
with per-stage diagnostics.

Usage:
    python -m rag.debug_retrieval "What is Zoro's bounty after Wano"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.retriever import retrieve, expand_query, lexical_score


def safe(text: str, length: int = 250) -> str:
    return text.encode("ascii", errors="replace").decode("ascii", errors="replace")[:length]


def main():
    query = (
        " ".join(sys.argv[1:])
        or "What is Zoro's bounty after Wano"
    )

    expanded = expand_query(query)

    from rag.retriever import _get_collection, ALIAS_MAP

    collection = _get_collection()

    # Fetch generous candidates so we can show all stages together
    raw = collection.query(
        query_texts=[expanded],
        n_results=30,
        include=["documents", "metadatas", "distances"],
    )

    candidates = []
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    distances = raw["distances"][0]
    for doc, meta, dist in zip(docs, metas, distances):
        candidates.append({
            "text": doc,
            "source": meta.get("source", ""),
            "heading": meta.get("heading", ""),
            "score": round(dist, 4),
        })

    # Stage: lexical rerank (same logic as retriever.retrieve)
    candidates.sort(
        key=lambda r: (
            lexical_score(r["text"], query),
            -r.get("score", 0),
        ),
        reverse=True,
    )

    # Stage: diversify (same logic as retriever.diversify)
    final = []
    counts: dict[str, int] = {}
    for c in candidates:
        src = c["source"]
        if counts.get(src, 0) < 2:
            counts[src] = counts.get(src, 0) + 1
            final.append(c)
        if len(final) == 10:
            break

    # Stage: retrieve() result (for comparison)
    production = retrieve(query)

    print(f"\nQuery: {query}")
    print(f"Expanded: {expanded}")
    print(f"Active aliases: {[k for k in ALIAS_MAP if k in query.lower()]}")
    print(f"Debug candidates: {len(final)} chunks (k=10, max_per_source=2)")
    print(f"Production retrieve():  {len(production)} chunks\n")

    print(f"{'#':<4} {'Source':<20} {'Lexical':<8} {'Score':<8} {'Pass':<6} Heading")
    print("-" * 80)
    seen_sources: set[str] = set()
    for i, r in enumerate(final, 1):
        ls = lexical_score(r["text"], query)
        heading = safe(r.get("heading") or "?", 55)
        is_first = r["source"] not in seen_sources
        seen_sources.add(r["source"])
        pass_label = "1st" if is_first else "2nd"
        print(
            f"{i:<4} {r['source']:<20} {ls:<8} {r['score']:<8} {pass_label:<6} {heading}"
        )

    print(f"\n--- Chunk previews ---\n")
    for i, r in enumerate(final, 1):
        text = safe(r["text"], 250).replace("\n", " ")
        print(f"[{i}] {r['source']} / {safe(r.get('heading', '?'), 55)}")
        print(f"    {text}")
        print()

    if len(production) != len(final):
        print(
            "Note: production retrieve() returned a different count. "
            "This may happen if the index was rebuilt between calls."
        )


if __name__ == "__main__":
    main()
