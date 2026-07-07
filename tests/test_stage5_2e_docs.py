from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2e_docs_define_fixture_only_boundary() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_ONLY.md").read_text(encoding="utf-8")
    assert "Stage 5.2E tests active gate writer in fixtures only" in doc
    assert "Real task gate writes remain disabled" in doc
    assert "No solver request files are created" in doc
    assert "TASK_FINAL_EVIDENCE_LEDGER.md remains untouched" in doc


def test_agents_mentions_stage5_2e_boundaries() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Active gate writer fixture support must not be treated as real approval" in text
    assert "Real task gates must not be written in Stage 5.2E" in text
    assert "No Approve Solver, Approve and Run, or Run Solver callbacks may be added" in text
