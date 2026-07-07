from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2i_docs_mention_preflight_is_not_execution_permission() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_VALIDATOR_WITHOUT_EXECUTION.md").read_text(encoding="utf-8")
    assert "Preflight pass is not solver execution permission" in doc
    assert "does not create active `solver_request.json`" in doc
    assert "does not create solver launchers, output execution directories" in doc
    assert "TASK_FINAL_EVIDENCE_LEDGER.md" in doc
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Stage 5.2I preflight pass must not be treated as solver execution permission" in agents
    assert "No solver_request.json may be written in Stage 5.2I" in agents
