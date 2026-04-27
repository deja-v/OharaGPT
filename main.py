"""
CLI entry point.

Usage:
    python main.py "Who is Roronoa Zoro?"

Each run gets a unique thread_id so checkpoints don't collide across questions.
The checkpoint DB is written to checkpoints.sqlite in the project root.
"""

import sys
import uuid

from langgraph.checkpoint.sqlite import SqliteSaver

from agent import build_graph

DB_PATH = "checkpoints.sqlite"


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<your One Piece question>\"")
        sys.exit(1)

    question = sys.argv[1]
    thread_id = str(uuid.uuid4())

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke({"question": question, "answer": ""}, config)

    print(f"\nQ: {question}")
    print(f"\nA: {result['answer']}")
    print(f"\n[thread_id: {thread_id}]")
    print(f"[checkpoint saved to {DB_PATH}]")


if __name__ == "__main__":
    main()
