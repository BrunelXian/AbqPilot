from __future__ import annotations

from abqpilot.gui.action_controller import GuiActionController


def test_acom_template_gui_actions_import_and_run(tmp_path) -> None:
    controller = GuiActionController(project_root=tmp_path)
    listed = controller.list_acom_templates()
    assert listed["success"] is True
    described = controller.describe_acom_template("mcpguard_review")
    assert described["details"]["requires_mcpguard"] is True
    generated = controller.generate_pipeline_acom_handoff(
        task_id="gui_acom_template",
        template_id="mcpguard_review",
    )
    assert generated["success"] is True
    validated = controller.validate_acom_template_pack()
    assert validated["verdict"] == "ACOM_TEMPLATE_PACK_VALID"
