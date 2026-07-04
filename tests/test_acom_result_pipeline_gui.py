from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.result_schema import empty_structured_result
from abqpilot.gui import actions
from abqpilot.gui.action_controller import GuiActionController


def test_gui_acom_result_actions_import_and_run(tmp_path) -> None:
    controller = GuiActionController(project_root=tmp_path)
    generated = controller.generate_pipeline_acom_handoff(
        task_id="gui_acom_result",
        template_id="mcpguard_review",
    )
    assert generated["success"] is True
    task_dir = Path(generated["task_dir"])
    payload = empty_structured_result(generated["task_id"], generated["handoff_id"])
    result_path = task_dir / "codex_result" / "structured_result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    intake = controller.intake_codex_result(task_dir / "codex_handoff", result_path)
    assert intake["verdict"] == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"
    report = controller.report_acom_result_intake(task_dir)
    assert report["verdict"] == "ACOM_RESULT_INTAKE_REPORT_READY"


def test_gui_actions_module_exposes_acom_result_helpers(tmp_path) -> None:
    controller = GuiActionController(project_root=tmp_path)
    generated = controller.generate_pipeline_acom_handoff(
        task_id="gui_actions_acom_result",
        template_id="docs_status_update",
    )
    task_dir = Path(generated["task_dir"])
    payload = empty_structured_result(generated["task_id"], generated["handoff_id"])
    (task_dir / "codex_result" / "structured_result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert actions.intake_acom_result(task_dir)["verdict"] == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"
    assert actions.report_acom_result_intake(task_dir)["verdict"] == "ACOM_RESULT_INTAKE_REPORT_READY"
