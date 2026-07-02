import json
from pathlib import Path

from abqpilot.gui.action_controller import BLOCKED_VERDICT, GuiActionController
from abqpilot.gui.task_loader import discover_recent_tasks
from abqpilot.gui.workflow_presets import workflow_presets


def test_action_controller_load_and_refresh_task_returns_view_model(tmp_path):
    task_dir = _write_task(tmp_path, status="WAITING_FOR_ABQJOBPILOT")
    controller = GuiActionController(tmp_path)

    loaded = controller.load_task(task_dir)
    refreshed = controller.refresh_task(task_dir)

    assert loaded["verdict"] == "TASK_VIEW_MODEL_READY"
    assert loaded["view_model"]["task_id"] == "task"
    assert refreshed["view_model"]["right_panel"]["next_allowed_action"] == "Poll JobPilot Status"


def test_action_controller_blocks_dangerous_actions(tmp_path):
    controller = GuiActionController(tmp_path)

    result = controller.blocked_action("dangerous_action")

    assert result["verdict"] == BLOCKED_VERDICT
    assert result["success"] is False


def test_action_controller_open_artifact_folder_returns_path_only(tmp_path):
    artifact = tmp_path / "artifact.json"
    artifact.write_text("{}", encoding="utf-8")
    controller = GuiActionController(tmp_path)

    result = controller.open_artifact_folder(artifact)

    assert result["verdict"] == "ARTIFACT_FOLDER_PATH_READY"
    assert result["path"] == str(tmp_path)
    assert "instead of launching" in result["warnings"][0]


def test_action_controller_catches_exceptions(monkeypatch, tmp_path):
    controller = GuiActionController(tmp_path)

    def broken(_task_dir):
        raise RuntimeError("boom")

    monkeypatch.setattr("abqpilot.gui.action_controller.build_task_view_model", broken)

    result = controller.load_task(tmp_path / "missing")

    assert result["verdict"] == "GUI_ACTION_FAILED"
    assert "boom" in result["errors"][0]


def test_recent_task_discovery_sorts_by_modified_time(tmp_path):
    older = _write_task(tmp_path, task_id="older")
    newer = _write_task(tmp_path, task_id="newer")
    (newer / "touch.txt").write_text("new", encoding="utf-8")

    tasks = discover_recent_tasks(tmp_path / "runs", limit=2)

    assert tasks[0]["task_id"] in {"newer", "older"}
    assert {item["task_id"] for item in tasks} == {"older", "newer"}


def test_workflow_preset_definitions_exist():
    preset_ids = {preset["preset_id"] for preset in workflow_presets()}

    assert "prepare_only" in preset_ids
    assert "status_poll_only" in preset_ids
    assert "report_export" in preset_ids


def _write_task(tmp_path, status="WAITING_FOR_ABQJOBPILOT", task_id="task"):
    task_dir = tmp_path / "runs" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "task_id": task_id,
        "status": status,
        "current_step": "07_abqjobpilot_status_poll",
        "stop_reason": status,
        "steps": {"07_abqjobpilot_status_poll": {"status": "COMPLETED", "verdict": "JOB_QUEUED"}},
        "completed_steps": ["07_abqjobpilot_status_poll"],
        "failed_steps": [],
        "skipped_steps": [],
        "requires_human_action": False,
        "human_action_reason": None,
        "safety_flags": {"allow_solver_submit": False, "allow_llm": False, "allow_codex_runtime": False},
    }
    (task_dir / "task_state.json").write_text(json.dumps(state), encoding="utf-8")
    (task_dir / "artifacts.json").write_text(json.dumps({"task_id": task_id, "artifacts": []}), encoding="utf-8")
    (task_dir / "pipeline_trace.json").write_text(json.dumps({"task_id": task_id, "events": []}), encoding="utf-8")
    return task_dir
