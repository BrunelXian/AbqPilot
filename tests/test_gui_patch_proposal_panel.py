import json

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui.app import AbqPilotGui


def test_gui_patch_proposal_panel_imports():
    assert AbqPilotGui is not None


def test_gui_real_patch_proposal_requires_confirmation(tmp_path):
    controller = GuiActionController(tmp_path)
    task = _task(tmp_path)

    result = controller.propose_patch_real(task, confirmed=False)

    assert result["verdict"] == "GUI_PATCH_CONTEXT_CONFIRMATION_REQUIRED"


def test_gui_mock_patch_proposal_writes_artifact(tmp_path):
    controller = GuiActionController(tmp_path)
    task = _task(tmp_path)

    result = controller.propose_patch_mock(task)

    assert result["success"] is True
    assert result["verdict"] in {"NO_ACTION", "INSUFFICIENT_EVIDENCE", "PATCH_PROPOSED", "HUMAN_REVIEW_ONLY"}


def test_gui_preview_patch_context(tmp_path):
    controller = GuiActionController(tmp_path)
    task = _task(tmp_path)

    result = controller.preview_patch_context(task)

    assert result["verdict"] == "LLM_PATCH_CONTEXT_READY"
    assert result["details"]["patch_context"]["task_id"] == "task"


def _task(tmp_path):
    task = tmp_path / "runs" / "tasks" / "task"
    task.mkdir(parents=True)
    (task / "task_state.json").write_text(json.dumps({"task_id": "task", "status": "PASS", "failed_steps": []}), encoding="utf-8")
    (task / "artifacts.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    analysis = task / "analysis"
    analysis.mkdir()
    (analysis / "repair_plan.json").write_text(
        json.dumps({"repair_required": False, "recommended_next_action": "Export Run Report"}),
        encoding="utf-8",
    )
    return task
