from __future__ import annotations

from pathlib import Path


ROOT = Path("D:/Projects/AbqPilot-v2")


def test_docs_mention_scaffold_only_no_auto_execution():
    text = (ROOT / "docs" / "ACOM_DOWNSTREAM_REVALIDATION.md").read_text(encoding="utf-8")
    assert "scaffold" in text.lower()
    assert "does not automatically execute downstream agents" in text
    assert "Codex summary is not final evidence" in text
