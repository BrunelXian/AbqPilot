from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_controlled_solver_human_gate_preview_docs_define_preview_boundary() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_HUMAN_GATE_PREVIEW.md").read_text(encoding="utf-8")
    assert "Stage 5.2B designs controlled solver gate preview and approval token schema only" in doc
    assert "It does not approve solver" in doc
    assert "It does not run solver" in doc
    assert "Future solver approval and future solver execution must be separate stages" in doc


def test_agents_mentions_solver_approval_execution_separation() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Controlled solver approval preview must not be treated as active approval" in text
    assert "No Approve Solver or Run Solver callbacks may be added" in text
    assert "solver approval and solver execution must remain separated" in text
