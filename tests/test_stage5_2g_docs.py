from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2g_docs_mention_draft_only_and_no_solver_request() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_WITHOUT_EXECUTION.md").read_text(encoding="utf-8")
    assert "draft-only future `ExecutionAgent` handoff" in doc
    assert "does not create an active execution handoff" in doc
    assert "does not create solver request files" in doc
    assert "Solver execution remains a future separate explicit stage" in doc
    assert "TASK_FINAL_EVIDENCE_LEDGER.md" in doc
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Stage 5.2G handoff draft must not be treated as active execution permission" in agents
    assert "No solver request may be created in Stage 5.2G" in agents
