from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_1d_docs_mention_read_only_and_no_external_open() -> None:
    docs = [
        ROOT / "docs" / "GUI_REPORT_VIEWER_ARTIFACT_PREVIEW.md",
        ROOT / "docs" / "GUI_TRACE_VIEWER_TIMELINE.md",
        ROOT / "AGENTS.md",
    ]
    for path in docs:
        assert path.exists(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    assert "read-only" in text.lower()
    assert "external editor" in text.lower() or "external programs" in text.lower()
    assert "flagged, not fixed" in text.lower()
    assert "TASK_FINAL_EVIDENCE_LEDGER.md" in text
