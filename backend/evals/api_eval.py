"""
API Eval — runs 10 QA questions via HTTP against the live server.
Usage (server must be running on :8000): python -m evals.api_eval
"""
import sys
import uuid
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.eval import EVAL_QUESTIONS, score_answer

BASE_URL = "http://localhost:8000/api"


def run_api_eval():
    try:
        httpx.get(f"{BASE_URL}/health", timeout=5).raise_for_status()
    except Exception as e:
        print(f"ERROR: server unreachable at {BASE_URL}/health\n  {e}")
        sys.exit(1)

    results = []
    with httpx.Client(timeout=60) as client:
        for i, (question, keywords, sources, fix) in enumerate(EVAL_QUESTIONS, 1):
            try:
                resp = client.post(
                    f"{BASE_URL}/chat",
                    json={"question": question, "thread_id": str(uuid.uuid4())},
                )
                resp.raise_for_status()
                answer = resp.json().get("answer", "")
                http_ok = True
            except Exception as e:
                answer, http_ok = f"ERROR: {e}", False
            symbol, kw_pass, cite_pass = score_answer(answer, keywords, sources)
            results.append((i, question, symbol, kw_pass, http_ok))
            print(f"  {symbol} Q{i}  HTTP={'OK' if http_ok else 'FAIL'}")

    passed = sum(1 for *_, s, _, _ in results if s == "P")
    http_ok_count = sum(1 for *_, _, _, h in results if h)
    gate = http_ok_count == 10 and passed >= 8
    print(
        f"\nHTTP OK: {http_ok_count}/10   Score: {passed}/10   "
        f"{'TARGET MET' if gate else 'X BELOW TARGET'}"
    )


if __name__ == "__main__":
    run_api_eval()
