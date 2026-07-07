from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2f_docs_define_real_gate_without_execution() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_REAL_HUMAN_GATE_WITHOUT_EXECUTION.md").read_text(encoding="utf-8")
    assert "Stage 5.2F creates a real human approval gate only for the dedicated smoke task" in doc
    assert "Arbitrary real task gate writing remains disabled" in doc
    assert "No solver request files are created" in doc
    assert "Solver execution remains a future separate explicit stage" in doc


def test_agents_mentions_stage5_2f_boundaries() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Stage 5.2F smoke gate must not be treated as permission to execute solver" in text
    assert "No arbitrary task gate writing is allowed in Stage 5.2F" in text
    assert "No Run Solver or Approve and Run callbacks may be added" in text
