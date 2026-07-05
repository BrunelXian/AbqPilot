from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_1f_docs_describe_non_final_gui_beta_readiness() -> None:
    docs = [
        ROOT / "docs" / "GUI_BETA_E2E_SAFE_WORKFLOW.md",
        ROOT / "docs" / "GUI_BETA.md",
        ROOT / "AGENTS.md",
    ]
    for path in docs:
        assert path.exists(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    assert "GUI beta readiness" in text
    assert "not final evidence" in text.lower()
    assert "does not execute recommended actions" in text
    assert "does not run solver" in text
    assert "does not open ODB" in text
    assert "does not call Codex CLI" in text
    assert "does not freeze" in text
    assert "callback-free" in text


def test_stage5_1f_gui_app_imports() -> None:
    import abqpilot.gui.app  # noqa: F401
