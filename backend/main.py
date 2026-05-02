"""
CLI entry point.

Usage (from repo root):
    python backend/main.py "Who is Roronoa Zoro?"
"""

import sys
import uuid
from pathlib import Path

# Allow `from agent.graph import ...` to resolve when running from the repo root.
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.graph import build_graph

load_dotenv(Path(__file__).parent / ".env")

DB_PATH = str(Path(__file__).parent / "checkpoints.sqlite")


def main():
    if len(sys.argv) < 2:
        print('Usage: python backend/main.py "<your One Piece question>"')
        sys.exit(1)

    question = sys.argv[1]
    thread_id = str(uuid.uuid4())

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke({"question": question, "context": [], "answer": ""}, config)

    print(f"\nQ: {question}")
    print(f"\nA: {result['answer']}")
    print(f"\n[thread_id: {thread_id}]")
    print(f"[checkpoint saved to {DB_PATH}]")


if __name__ == "__main__":
    main()
