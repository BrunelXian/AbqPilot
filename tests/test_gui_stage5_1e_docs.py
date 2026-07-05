from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_1e_docs_describe_advisory_recommendations_only() -> None:
    docs = [
        ROOT / "docs" / "GUI_GUIDED_NEXT_STEP_RECOMMENDATION.md",
        ROOT / "docs" / "GUI_BETA.md",
        ROOT / "AGENTS.md",
    ]
    for path in docs:
        assert path.exists(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    assert "advisory" in text.lower()
    assert "generic execute" in text.lower()
    assert "GUI does not call Codex CLI" in text
    assert "Final evidence remains locked" in text
    assert "does not approve final evidence" in text
