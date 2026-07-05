from __future__ import annotations

from pathlib import Path


ROOT = Path("D:/Projects/AbqPilot-v2")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_stage5_1b_docs_mention_visual_readability_only():
    text = _read("docs/GUI_VISUAL_LAYOUT_READABILITY.md")
    assert "Stage 5.1B polishes" in text
    assert "does not add new execution capability" in text
    assert "Disabled high-risk actions remain visible but callback-free" in text


def test_stage5_1b_docs_mention_no_execution_capability():
    text = _read("docs/GUI_BETA.md") + "\n" + _read("docs/GUI_SAFE_WORKFLOW_UX.md")
    assert "visual/readability only" in text
    assert "adds no new solver, ODB, Codex, queue, scheduling, final evidence, or final verdict capability" in text
    assert "callback-free" in text


def test_agents_stage5_1b_rules_present():
    text = _read("AGENTS.md")
    assert "GUI visual polish must not weaken safety boundaries" in text
    assert "GUI must not present disabled actions as executable" in text
    assert "GUI copy must distinguish non-final/non-solver records from final evidence" in text
