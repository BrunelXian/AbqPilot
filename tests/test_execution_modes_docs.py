from __future__ import annotations

from pathlib import Path


ROOT = Path("D:/Projects/AbqPilot-v2")


def test_execution_mode_docs_mention_acom_and_narm():
    text = (ROOT / "docs" / "EXECUTION_MODES.md").read_text(encoding="utf-8")
    assert "ACOM" in text
    assert "NARM" in text
    assert "Codex summaries are not final evidence" in text


def test_agents_mentions_acom_default_and_condition_preservation():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Default execution direction is ACOM" in text
    assert "Codex summaries are not final evidence" in text
    assert "non-target original model conditions are preserved" in text
