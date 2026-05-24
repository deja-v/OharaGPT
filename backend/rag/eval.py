"""
RAG Evaluation Harness — runs 10 canonical questions through the live agent,
scores answers against expected keywords, and prints a fix suggestion for
each failing question.

Usage (from backend/):
    python -m rag.eval
    python -m rag.eval --no-rag      # scores LLM-only baseline (skips retrieve node)
"""

import sys
import uuid
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv(Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Eval dataset
# Each entry: (question, expected_keywords, source_hints, fix_suggestion)
#   expected_keywords  — ALL must appear in answer (case-insensitive) for
#   source_hints       — at least ONE must appear in answer for citation check
#   fix_suggestion     — printed when this question fails, guiding next steps
# ---------------------------------------------------------------------------
EVAL_QUESTIONS = [
    (
        "What is Dorry's exact bounty?",
        ["100,000,000"],
        ["dorry", "bounty"],
        (
            "Q1 FAIL — Dorry's bounty not retrieved.\n"
            "  Check: does backend/data/raw/bounty.md mention '100,000,000' and 'Dorry'?\n"
            "  If not, Dorry has no dedicated page — add a Giants or Dorry page to PAGES in scrape.py,\n"
            "  or check if the general 'bounty' wiki page lists minor character bounties.\n"
            "  Then re-scrape and re-index."
        ),
    ),
    (
        "What was Roronoa Zoro's bounty after the Wano arc?",
        ["1,111,000,000"],
        ["zoro"],
        (
            "Q2 FAIL — Zoro's post-Wano bounty not retrieved.\n"
            "  Check: grep -i '1,111' backend/data/raw/zoro.md\n"
            "  If missing, the infobox scraper fix may not have run — delete zoro.md,\n"
            "  re-run python -m rag.scrape, then python -m rag.index --force.\n"
            "  Also run: python -m rag.debug_retrieval \"Zoro bounty after Wano\""
        ),
    ),
    (
        "What is the official name of Luffy's devil fruit?",
        ["hito hito no mi", "nika"],
        ["nika_fruit", "luffy"],
        (
            "Q3 FAIL — Returning 'Gomu Gomu no Mi' instead of 'Hito Hito no Mi, Model: Nika'.\n"
            "  Check expand_query() in retriever.py — ALIAS_MAP must contain 'gomu gomu'.\n"
            "  Check diversify() is active in retrieve().\n"
            "  Run: python -m rag.debug_retrieval \"official name of Luffy devil fruit\"\n"
            "  nika_fruit must appear in top 6 results."
        ),
    ),
    (
        "What happened during the Void Century?",
        ["800", "void century"],
        ["void_century"],
        (
            "Q4 FAIL — Void Century facts not retrieved or answer is fabricated.\n"
            "  Check: does backend/data/raw/void_century.md exist and have content?\n"
            "  Check the system prompt instructs the LLM to distinguish confirmed vs unconfirmed.\n"
            "  Run: python -m rag.debug_retrieval \"Void Century what happened\""
        ),
    ),
    (
        "What are the three Ancient Weapons and who is Poseidon?",
        ["pluton", "poseidon", "uranus", "shirahoshi"],
        ["ancient_weapons"],
        (
            "Q5 FAIL — Ancient Weapons or Poseidon identity wrong/missing.\n"
            "  Check: backend/data/raw/ancient_weapons.md must mention all three weapons\n"
            "  and name Shirahoshi as Poseidon.\n"
            "  Run: python -m rag.debug_retrieval \"three Ancient Weapons Poseidon\""
        ),
    ),
    (
        "What promise did Shanks make when he gave Luffy his hat?",
        ["hat", "pirate"],
        ["luffy", "shanks"],
        (
            "Q6 FAIL — Shanks hat promise not retrieved correctly.\n"
            "  Check: backend/data/raw/shanks.md and luffy.md for the hat promise scene.\n"
            "  The exact phrasing should be present. If vague, the scraper may have\n"
            "  stripped the relevant story section. Check section headings in those files.\n"
            "  Run: python -m rag.debug_retrieval \"Shanks promise hat Luffy\""
        ),
    ),
    (
        "What is the advanced form of Conqueror's Haki introduced in Wano?",
        ["coat"],
        ["conquerors_haki"],
        (
            "Q7 FAIL — Advanced Conqueror's Haki (coating) not retrieved.\n"
            "  Check: backend/data/raw/conquerors_haki.md for 'coat' or 'advanced'.\n"
            "  This is a recent Wano reveal — if the wiki section is thin, the chunk\n"
            "  may be too small (< 100 chars) and filtered out at index time.\n"
            "  Check MIN_CHUNK_SIZE in index.py — try lowering it to 50 for this pass.\n"
            "  Run: python -m rag.debug_retrieval \"advanced Conqueror Haki coating Wano\""
        ),
    ),
    (
        "Who are the Five Elders and what is their role?",
        ["five elders", "world government"],
        ["five_elders"],
        (
            "Q8 FAIL — Five Elders info not retrieved.\n"
            "  Check: backend/data/raw/five_elders.md exists and has their names + roles.\n"
            "  Also check that 'five_elders' page was successfully scraped (not 404).\n"
            "  Run: python -m rag.debug_retrieval \"Five Elders role World Government\""
        ),
    ),
    (
        "What is the immortality operation that Trafalgar Law's devil fruit can perform?",
        ["perennial youth", "lifespan"],
        ["ope_ope", "law"],
        (
            "Q9 FAIL — Perennial Youth Operation details not retrieved.\n"
            "  Check: backend/data/raw/ope_ope.md for 'perennial youth' and 'lifespan'.\n"
            "  These terms must appear verbatim for the keyword check to pass.\n"
            "  Run: python -m rag.debug_retrieval \"Law immortality operation Ope Ope\""
        ),
    ),
    (
        "What is the relationship between Joy Boy, the Sun God Nika, and Luffy?",
        ["joy boy", "nika", "luffy"],
        ["joy_boy", "nika_fruit"],
        (
            "Q10 FAIL — Joy Boy / Nika / Luffy connection not retrieved or conflated.\n"
            "  Check: both joy_boy.md and nika_fruit.md exist and mention each other.\n"
            "  diversify() should pull chunks from both pages for this query.\n"
            "  Check the system prompt instructs LLM to separate confirmed vs interpreted facts.\n"
            "  Run: python -m rag.debug_retrieval \"Joy Boy Sun God Nika Luffy relationship\""
        ),
    ),
]

DB_PATH = str(Path(__file__).parent.parent / "checkpoints.sqlite")


def score_answer(answer: str, keywords: list[str], sources: list[str]) -> tuple[str, bool, bool]:
    a = answer.lower()
    keywords_pass = all(kw.lower() in a for kw in keywords)
    citation_pass = any(src.lower() in a for src in sources)

    if keywords_pass and citation_pass:
        return "P", True, True
    elif keywords_pass or citation_pass:
        return "~", keywords_pass, citation_pass
    else:
        return "X", False, False


def run_eval(use_rag: bool = True):
    mode = "WITH RAG" if use_rag else "WITHOUT RAG (baseline)"
    print(f"\n{'='*60}")
    print(f"  OharaGPT Eval — {mode}")
    print(f"{'='*60}\n")

    from agent.graph import build_graph, build_graph_no_rag

    graph_fn = build_graph if use_rag else build_graph_no_rag

    results = []
    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = graph_fn(checkpointer)

        for i, (question, keywords, sources, fix) in enumerate(EVAL_QUESTIONS, 1):
            print(f"Running Q{i}: {question[:60]}...")
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            try:
                state = graph.invoke(
                    {"question": question, "context": [], "answer": ""},
                    config,
                )
                answer = state.get("answer") or state.get("response") or ""
            except Exception as e:
                answer = f"ERROR: {e}"

            symbol, kw_pass, cite_pass = score_answer(answer, keywords, sources)
            results.append((i, question, answer, symbol, kw_pass, cite_pass, fix))
            print(f"  {symbol} Q{i}")

    # --- Print scoring table ---
    print(f"\n{'='*60}")
    print(f"  SCORING TABLE — {mode}")
    print(f"{'='*60}")
    print(f"{'#':<4} {'Status':<6} {'Keywords':<10} {'Cited':<8} Question")
    print("-" * 60)

    passed = 0
    failing_fixes = []
    for i, question, answer, symbol, kw_pass, cite_pass, fix in results:
        kw_str  = "Y" if kw_pass  else "X"
        cit_str = "Y" if cite_pass else "X"
        print(f"Q{i:<3} {symbol:<6} {kw_str:<10} {cit_str:<8} {question[:45]}")
        if symbol == "P":
            passed += 1
        else:
            failing_fixes.append((i, answer[:200], fix))

    print("-" * 60)
    print(f"TOTAL: {passed}/10   {' TARGET MET' if passed >= 7 else 'X BELOW TARGET (need >=7/10)'}\n")

    # --- Print answers + fix suggestions for failures ---
    if failing_fixes:
        print(f"\n{'='*60}")
        print("  FIX SUGGESTIONS FOR FAILING QUESTIONS")
        print(f"{'='*60}")
        for i, answer_snippet, fix in failing_fixes:
            print(f"\n--- Q{i} ---")
            print(f"Agent answered: \"{answer_snippet}...\"")
            print(fix)

    return passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-rag", action="store_true", help="Run baseline without retrieval")
    args = parser.parse_args()
    run_eval(use_rag=not args.no_rag)


if __name__ == "__main__":
    main()
