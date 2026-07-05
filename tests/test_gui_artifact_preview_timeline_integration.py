from pathlib import Path

from abqpilot.gui.trace_detail_cards import build_trace_detail_card


def test_timeline_detail_card_attaches_artifact_preview_models(tmp_path: Path) -> None:
    task = tmp_path / "task"
    (task / "trace").mkdir(parents=True)
    (task / "handoffs").mkdir()
    (task / "gates").mkdir()
    (task / "codex_handoff").mkdir()
    (task / "codex_handoff" / "handoff_manifest.json").write_text('{"task_id":"task"}', encoding="utf-8")
    (task / "trace" / "RUN_001_ACOM_MCPGUARD_REVIEW.md").write_text(
        """---
doc_type: run_report
task_id: task
run_id: RUN_001
run_name: ACOM_MCPGUARD_REVIEW
agent: ACOMAgent
status: ACOM_HANDOFF_READY
risk_level: LOW
forbidden_actions: {}
---
# Run
""",
        encoding="utf-8",
    )
    card = build_trace_detail_card(task, "acom_handoff")
    assert card["read_only"] is True
    assert card["action_allowed"] is False
    assert card["artifact_previews"]
    assert all(item["read_only"] is True for item in card["artifact_previews"])
