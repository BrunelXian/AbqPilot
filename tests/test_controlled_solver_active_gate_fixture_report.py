from pathlib import Path

from abqpilot.gui.controlled_solver_active_gate_card import build_controlled_solver_active_gate_card
from abqpilot.gui.controlled_solver_active_gate_fixture_report import (
    render_fixture_writer_policy,
    render_fixture_writer_report,
    write_active_gate_writer_fixture_report,
)


def test_fixture_report_module_imports_and_outputs(tmp_path: Path) -> None:
    result = write_active_gate_writer_fixture_report(tmp_path)
    assert result["verdict"] == "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_POLICY_REPORT_READY"
    for path in result["output_paths"].values():
        assert Path(path).exists()
    details = result["details"]
    assert details["fixture_write_supported"] is True
    assert details["real_task_write_enabled"] is False
    assert details["real_task_write_attempt_blocked"] is True
    assert details["solver_request_created"] is False
    assert details["no_real_task_gate_written"] is True
    assert "TEST_FIXTURE_ONLY" in render_fixture_writer_policy()
    assert "fixtures only" in render_fixture_writer_report(details)


def test_gui_card_mentions_fixture_only_and_callback_free(tmp_path: Path) -> None:
    card = build_controlled_solver_active_gate_card(tmp_path)
    assert card["fixture_writer_title"] == "Active Gate Writer [TEST FIXTURE ONLY]"
    assert card["real_task_writes_disabled"] is True
    assert card["backend_callback"] is None
    assert "real task writes disabled" in card["required_copy"]
    assert "Human approval does not execute solver" in card["required_copy"]
