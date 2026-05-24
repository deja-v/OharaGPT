"""
One-shot indexer.

Usage (from repo root):
    python -m rag.index

Reads all .md files from backend/data/raw/, splits each into sections using
H2/H3 headers, embeds with sentence-transformers, and stores in a Chroma
collection at backend/data/index/.

Idempotent: if the collection already exists with the same number of chunks,
it exits early. Pass --force to re-index from scratch.
"""

import sys
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
COLLECTION_NAME = "op_wiki"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Minimum characters a chunk must have to be worth indexing
MIN_CHUNK_CHARS = 50


def split_into_sections(md_text: str, source_file: str) -> list[dict[str, str]]:
    """
    Split a Markdown document into chunks at H2/H3 boundaries.

    Each chunk carries:
      - text: the section heading + its body
      - source: filename stem (used as the wiki page reference)
      - heading: the section heading text
    """
    # Split on lines that start with ## or ###
    pattern = re.compile(r"^(#{2,3} .+)$", re.MULTILINE)
    positions = [m.start() for m in pattern.finditer(md_text)]

    if not positions:
        # No sub-headers — return the whole document as one chunk
        return [{"text": md_text.strip(), "source": source_file, "heading": source_file}]

    chunks = []
    # Content before the first H2/H3
    preamble = md_text[: positions[0]].strip()
    if len(preamble) >= MIN_CHUNK_CHARS:
        chunks.append({"text": preamble, "source": source_file, "heading": "Introduction"})

    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(md_text)
        section_text = md_text[pos:end].strip()
        if len(section_text) >= MIN_CHUNK_CHARS:
            heading_line = md_text[pos : md_text.index("\n", pos)].strip("# ").strip()
            chunks.append({
                "text": section_text,
                "source": source_file,
                "heading": heading_line,
            })

    return chunks


def load_all_chunks() -> list[dict[str, str]]:
    chunks = []
    md_files = sorted(RAW_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {RAW_DIR}")
        print("Run `python -m rag.scrape` first.")
        sys.exit(1)

    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        file_chunks = split_into_sections(text, md_path.stem)
        chunks.extend(file_chunks)
        print(f"  {md_path.stem}: {len(file_chunks)} chunks")

    return chunks


def build_index(force: bool = False):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    if force:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("Deleted existing collection.")
        except Exception:
            pass

    print(f"\nLoading chunks from {RAW_DIR} ...\n")
    chunks = load_all_chunks()
    print(f"\nTotal chunks: {len(chunks)}")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    existing_count = collection.count()
    # Idempotency check is count-based (not content-based). If source files change
    # such that the net chunk count stays the same (e.g. add one page, delete another),
    # this check passes incorrectly and the stale index is kept. Use --force to override.
    if not force and existing_count == len(chunks):
        print(f"\nCollection already has {existing_count} chunks — nothing to do.")
        print("Pass --force to re-index.")
        return

    if existing_count > 0:
        # Clear and re-add so IDs stay consistent
        existing_ids = collection.get()["ids"]
        collection.delete(ids=existing_ids)

    print(f"\nEmbedding and storing {len(chunks)} chunks ...")
    batch_size = 64
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.add(
            ids=[f"{c['source']}::{c['heading']}::{i + j}" for j, c in enumerate(batch)],
            documents=[c["text"] for c in batch],
            metadatas=[{"source": c["source"], "heading": c["heading"]} for c in batch],
        )
        print(f"  stored {min(i + batch_size, len(chunks))}/{len(chunks)}")

    print(f"\nIndex built. Collection '{COLLECTION_NAME}' has {collection.count()} chunks.")
    print(f"Location: {INDEX_DIR}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-index even if collection exists")
    args = parser.parse_args()
    build_index(force=args.force)


if __name__ == "__main__":
    main()
