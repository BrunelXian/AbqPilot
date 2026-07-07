from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2d_docs_define_active_gate_design_boundary() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_ACTIVE_HUMAN_GATE_RECORD_DESIGN.md").read_text(encoding="utf-8")
    assert "Stage 5.2D defines active controlled solver human gate record design only" in doc
    assert "It does not write a real active gate to any real task" in doc
    assert "Token consumption does not execute solver" in doc
    assert "Solver execution must be a later explicit stage" in doc


def test_agents_mentions_stage5_2d_boundaries() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Active controlled solver gate design must not be treated as real approval in Stage 5.2D" in text
    assert "No active real task gates may be written in Stage 5.2D" in text
    assert "No Approve Solver, Approve and Run, or Run Solver callbacks may be added" in text
