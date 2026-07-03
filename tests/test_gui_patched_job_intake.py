from abqpilot.gui.action_controller import GuiActionController


def test_gui_patched_job_actions_import(tmp_path):
    controller = GuiActionController(project_root=tmp_path)

    assert hasattr(controller, "intake_patched_job_output")
    assert hasattr(controller, "extract_patched_job_metrics")
    assert hasattr(controller, "report_patched_job")


def test_gui_patched_job_missing_workflow_fails_safe(tmp_path):
    controller = GuiActionController(project_root=tmp_path)

    result = controller.intake_patched_job_output(tmp_path / "missing")

    assert result["success"] is True
    assert result["verdict"] == "WAITING_FOR_PATCHED_JOB"
    assert result["details"]["opened_odb"] is False
