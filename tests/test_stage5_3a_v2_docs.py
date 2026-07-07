from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stage5_3a_v2_docs_and_guard_policy() -> None:
    doc = (ROOT / "docs" / "CONTROLLED_SOLVER_DEMO_SMOKE_RUN.md").read_text(encoding="utf-8")
    guard = (ROOT / "docs" / "WORKSPACE_ROOT_GUARD.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Stage 5.3A-v2" in doc
    assert "first controlled Abaqus invocation" in doc
    assert "does not open ODB" in doc
    assert "Metrics" in doc
    assert "final evidence" in doc
    assert "forbidden-root pre-scan has zero hits" in guard
    assert "Stage 5.3A-v2 controlled solver demo smoke" in agents
    assert "No generic Run Solver" in agents
