from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2c_docs_define_inactive_draft_boundary() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_INACTIVE_HUMAN_GATE_DRAFT.md").read_text(encoding="utf-8")
    assert "Stage 5.2C creates an inactive controlled solver human gate draft only" in doc
    assert "It does not write active task `gates/` records" in doc
    assert "Future active human approval gate creation must be a separate explicit stage" in doc
    assert "Future solver execution must be a later separate explicit stage" in doc


def test_agents_mentions_inactive_gate_draft_boundaries() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Inactive controlled solver gate draft must not be treated as active approval" in text
    assert "No Approve Solver, Create Active Gate, or Run Solver callbacks may be added" in text
    assert "solver approval and solver execution must remain separated" in text
