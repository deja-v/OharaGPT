"""
Theory Verification Eval — 5 questions with expected verdicts.
Usage: python -m evals.theory_eval
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv(Path(__file__).parent.parent / ".env")

THEORY_QUESTIONS = [
    {
        "question": "Theory: Jewelry Bonney is Bartholomew Kuma's biological daughter",
        "expected_verdict": "SUPPORTED",
        "must_mention": ["bonney", "kuma"],
        "rationale": "Confirmed in chapter 1099",
    },
    {
        "question": "Theory: Gol D. Roger had a devil fruit power",
        "expected_verdict": "CONTRADICTED",
        "must_mention": ["roger"],
        "rationale": "Roger had no devil fruit; confirmed in canon",
    },
    {
        "question": "Is it possible that Shanks is secretly working for the World Government?",
        "expected_verdict": "INSUFFICIENT",
        "must_mention": ["shanks"],
        "rationale": "Only circumstantial evidence; no confirmed statement",
    },
    {
        "question": "Theory: Luffy is the reincarnation of Joy Boy",
        "expected_verdict": "SUPPORTED",
        "must_mention": ["luffy", "joy boy"],
        "rationale": "Zunesha confirms this in chapter 1044",
    },
    {
        "question": "What if Im-sama is kept alive by the Ope Ope no Mi's immortality operation?",
        "expected_verdict": "INSUFFICIENT",
        "must_mention": ["im"],
        "rationale": "Speculative; wiki doesn't confirm the mechanism",
    },
]

DB_PATH = str(Path(__file__).parent.parent / "checkpoints.sqlite")


def score_theory(answer, expected_verdict, must_mention):
    v_pass = expected_verdict.upper() in answer.upper()
    m_pass = all(m.lower() in answer.lower() for m in must_mention)
    if v_pass and m_pass:
        return "P", True, True
    if v_pass or m_pass:
        return "~", v_pass, m_pass
    return "X", False, False


def run_theory_eval():
    from agent.graph import build_graph

    results = []
    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)
        for i, q in enumerate(THEORY_QUESTIONS, 1):
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            try:
                state = graph.invoke({"question": q["question"]}, config)
                answer = state.get("answer", "")
                verdict = state.get("verdict", "")
            except Exception as e:
                answer, verdict = f"ERROR: {e}", ""
            symbol, v_pass, m_pass = score_theory(
                f"{verdict} {answer}",
                q["expected_verdict"],
                q["must_mention"],
            )
            results.append((i, q, answer, verdict, symbol, v_pass, m_pass))
            print(f"  {symbol} Q{i} — verdict: {verdict or '(none)'}")

    passed = sum(1 for *_, s, _, _ in results if s == "P")
    print(
        f"\nTOTAL: {passed}/5   "
        f"{'TARGET MET' if passed >= 3 else 'X BELOW TARGET (need >=3/5)'}"
    )
    return passed


if __name__ == "__main__":
    run_theory_eval()
