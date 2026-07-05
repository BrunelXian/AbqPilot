from __future__ import annotations

from pathlib import Path


def test_non_solver_evidence_summary_docs_define_non_final_boundary():
    text = Path("docs/NON_SOLVER_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Stage 5.0H" in text
    assert "non-final and non-solver only" in text
    assert "does not update `TASK_FINAL_EVIDENCE_LEDGER.md`" in text
    assert "does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict" in text


def test_agents_md_mentions_evidence_report_agent_non_solver_boundary():
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "EvidenceReportAgent may summarize NON_SOLVER_EVIDENCE_LEDGER" in text
    assert "must not convert non-solver evidence into final evidence" in text
    assert "must not update TASK_FINAL_EVIDENCE_LEDGER.md in Stage 5.0H" in text
