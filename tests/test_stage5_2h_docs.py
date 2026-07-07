from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2h_docs_mention_draft_schema_and_no_active_request() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_WITHOUT_EXECUTION.md").read_text(encoding="utf-8")
    assert "draft schema for a future controlled solver request" in doc
    assert "does not create active `solver_request.json`" in doc
    assert "does not create `job_request.json`, `abaqus_job.json`" in doc
    assert "Solver execution remains a future separate explicit stage" in doc
    assert "TASK_FINAL_EVIDENCE_LEDGER.md" in doc
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Stage 5.2H request draft must not be treated as an active solver request" in agents
    assert "No solver_request.json may be written in Stage 5.2H" in agents
