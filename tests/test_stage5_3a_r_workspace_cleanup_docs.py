from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_3a_r_workspace_guard_docs() -> None:
    doc = (ROOT / "docs" / "WORKSPACE_ROOT_GUARD.md").read_text(encoding="utf-8")
    assert "D:\\Projects\\AbqPilot-v2" in doc
    assert "D:\\Users\\wuxia\\Documents\\AbqPilot" in doc
    assert "apply_patch" in doc
    assert "current working directory" in doc
    assert "explicit human approval" in doc

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Stage 5.3A-R workspace remediation" in agents
    assert "Relative patch paths must not be used" in agents
