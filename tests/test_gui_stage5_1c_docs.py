from __future__ import annotations

from pathlib import Path


ROOT = Path("D:/Projects/AbqPilot-v2")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_stage5_1c_docs_mention_read_only_trace_viewer():
    text = _read("docs/GUI_TRACE_VIEWER_TIMELINE.md")
    assert "read-only GUI trace viewer" in text
    assert "Timeline selection is read-only" in text
    assert "Final evidence remains locked" in text


def test_stage5_1c_docs_mention_no_execution():
    text = _read("docs/GUI_BETA.md") + "\n" + _read("docs/PIPELINE_TRACE_HANDOFF_GATE_PROTOCOL.md")
    assert "Timeline selection does not execute" in text
    assert "run solver" in text
    assert "open ODB" in text
    assert "call Codex CLI" in text


def test_stage5_1c_agents_rules_present():
    text = _read("AGENTS.md")
    assert "GUI trace viewer must be read-only" in text
    assert "Timeline interaction must not execute backend actions" in text
    assert "Viewer must flag but not modify unsafe final approval claims" in text
    assert "Viewer must preserve final evidence locked state" in text
