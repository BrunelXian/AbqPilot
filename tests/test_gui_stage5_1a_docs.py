from __future__ import annotations

from pathlib import Path


ROOT = Path("D:/Projects/AbqPilot-v2")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_gui_docs_mention_final_evidence_locked_and_disabled_paths():
    text = _read("docs/GUI_INFORMATION_ARCHITECTURE.md") + "\n" + _read("docs/GUI_SAFE_WORKFLOW_UX.md")
    assert "Final evidence remains locked" in text
    assert "does not call Codex CLI" in text
    assert "does not run solver" in text
    assert "does not open ODB" in text
    assert "Queue" in text


def test_existing_gui_docs_mention_stage5_1a_boundaries():
    text = _read("docs/GUI_BETA.md")
    assert "Stage 5.1A reorganizes GUI information architecture" in text
    assert "no executable backend callback" in text
    assert "does not call Codex CLI" in text
    assert "run solver" in text
    assert "open ODB" in text


def test_agents_mentions_gui_stage5_1a_rules():
    text = _read("AGENTS.md")
    assert "GUI must not present non-solver acknowledgement as final evidence" in text
    assert "GUI disabled high-risk actions must not have executable backend callbacks" in text
    assert "GUI must preserve RUN/HANDOFF/GATE protocol visibility" in text
    assert "GUI must display final evidence locked" in text
