from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docs_mention_acom_templates_on_pipeline_protocol() -> None:
    docs = [
        ROOT / "docs" / "ACOM_TASK_TEMPLATES.md",
        ROOT / "docs" / "ACOM_PIPELINE_INTEGRATION.md",
        ROOT / "docs" / "ACOM_MODE.md",
        ROOT / "docs" / "PIPELINE_COMMUNICATION_PROTOCOL.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "ACOM" in text
        assert "pipeline" in text.lower()
        assert "Codex" in text
        assert "not final evidence" in text


def test_agents_forbids_isolated_codex_prompts() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Do not generate isolated Codex prompts without pipeline trace" in text
    assert "Do not auto-call Codex" in text
