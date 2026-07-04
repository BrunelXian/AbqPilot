from __future__ import annotations

from abqpilot.gui.action_controller import GuiActionController


def test_pipeline_protocol_gui_actions_import_and_run(tmp_path) -> None:
    controller = GuiActionController(project_root=tmp_path)
    listed = controller.list_pipeline_agents()
    assert listed["success"] is True
    assert "PipelineSupervisor" in listed["details"]["agents"]
    scaffolded = controller.scaffold_pipeline_task("gui_pipeline_smoke")
    assert scaffolded["success"] is True
    task_dir = scaffolded["details"]["task_dir"]
    validated = controller.validate_pipeline_protocol(task_dir)
    assert validated["verdict"] == "PIPELINE_PROTOCOL_VALID"
    reported = controller.report_pipeline_protocol(task_dir)
    assert reported["verdict"] == "PIPELINE_PROTOCOL_REPORT_READY"
