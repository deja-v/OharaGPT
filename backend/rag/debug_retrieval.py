"""
Debug retrieval: shows exactly what chunks are returned for a query.

Usage:
    python -m rag.debug_retrieval "What is Zoro's bounty after Wano"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.retriever import retrieve


def main():
    query = (
        " ".join(sys.argv[1:])
        or "What is Zoro's bounty after Wano"
    )

    results = retrieve(query, k=8)

    print(f"\nQuery: {query}")
    print(f"Retrieved {len(results)} chunks:\n")

    for i, r in enumerate(results, 1):
        score = r.get("score", "?")
        score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
        print(
            f"[{i}] "
            f"source={r['source']} | "
            f"heading={r.get('heading', '?')} | "
            f"score={score_str}"
        )

        text = r['text'][:300].strip()
        print(f"    {text.encode('ascii', 'replace').decode('ascii')}")
        print()


if __name__ == "__main__":
    main()
