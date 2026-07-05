from __future__ import annotations

from pathlib import Path


def test_supervisor_non_solver_summary_ack_docs_define_boundary():
    text = Path("docs/PIPELINE_SUPERVISOR_NON_SOLVER_SUMMARY_ACK.md").read_text(encoding="utf-8")
    assert "Stage 5.0I" in text
    assert "non-final and non-solver only" in text
    assert "does not update `TASK_FINAL_EVIDENCE_LEDGER.md`" in text
    assert "does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict" in text


def test_agents_md_mentions_summary_ack_boundary():
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "PipelineSupervisor may acknowledge non-solver summary records into NON_SOLVER_SUMMARY_ACK_LEDGER" in text
    assert "must not convert non-solver summaries into final evidence" in text
    assert "must not update TASK_FINAL_EVIDENCE_LEDGER.md in Stage 5.0I" in text
