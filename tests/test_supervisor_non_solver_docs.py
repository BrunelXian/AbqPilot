from __future__ import annotations

from pathlib import Path


def test_supervisor_non_solver_docs_define_non_final_ledger():
    text = Path("docs/PIPELINE_SUPERVISOR_NON_SOLVER_REVIEW.md").read_text(encoding="utf-8")
    assert "non-solver evidence ledger" in text.lower()
    assert "does not approve solver" in text
    assert "does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict" in text


def test_agents_md_mentions_supervisor_non_solver_review_boundary():
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "NON_SOLVER_EVIDENCE_LEDGER" in text
    assert "must not freeze final evidence" in text
    assert "must not approve solver, ODB, metrics" in text
