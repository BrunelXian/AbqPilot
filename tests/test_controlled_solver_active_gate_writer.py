from abqpilot.gui.controlled_solver_active_gate_writer import write_controlled_solver_active_gate_record_disabled


def test_active_gate_writer_disabled_in_stage5_2d(tmp_path) -> None:
    result = write_controlled_solver_active_gate_record_disabled(tmp_path, {"doc_type": "gate_decision"})
    assert result["writer_status"] == "ACTIVE_GATE_WRITER_DISABLED_IN_STAGE_5_2D"
    assert result["writer_enabled"] is False
    assert result["real_project_gate_written"] is False
    assert result["active_task_gate_record_written"] is False
    assert result["solver_request_created"] is False
    assert not (tmp_path / "gates").exists()
