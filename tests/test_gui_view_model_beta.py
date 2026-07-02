import json

from abqpilot.ui_state.view_model import build_task_view_model


def test_right_panel_prioritizes_failed_step(tmp_path):
    task_dir = _write_task(tmp_path, status="FAILED")

    model = build_task_view_model(task_dir)

    assert model["current_module"] == "odb_metrics"
    assert model["right_panel"]["module_name"] == "ODB Metrics"
    assert "Review artifacts" in model["right_panel"]["next_allowed_action"]


def test_right_panel_maps_approval_required_to_token_action(tmp_path):
    task_dir = _write_task(tmp_path, status="APPROVAL_REQUIRED", failed=False)

    model = build_task_view_model(task_dir)

    assert model["current_module"] == "human_approval"
    assert model["right_panel"]["next_allowed_action"] == "Create Approval Token"


def test_right_panel_maps_job_output_ready_to_continuation(tmp_path):
    task_dir = _write_task(tmp_path, status="JOB_OUTPUTS_READY", failed=False)

    model = build_task_view_model(task_dir)

    assert model["right_panel"]["next_allowed_action"] == "Continue From Job Output"


def _write_task(tmp_path, status, failed=True):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    task_dir.mkdir(parents=True)
    steps = {
        "07_abqjobpilot_status_poll": {"status": "COMPLETED", "verdict": "JOB_QUEUED"},
        "09_odb_metrics": {"status": "FAILED" if failed else "PENDING", "verdict": "NEED_ODB_METRICS_JSON" if failed else None},
    }
    state = {
        "task_id": "task",
        "status": status,
        "current_step": "07_abqjobpilot_status_poll",
        "stop_reason": status,
        "steps": steps,
        "completed_steps": ["07_abqjobpilot_status_poll"],
        "failed_steps": ["09_odb_metrics"] if failed else [],
        "skipped_steps": [],
        "requires_human_action": False,
        "human_action_reason": None,
        "safety_flags": {"allow_solver_submit": False, "allow_llm": False, "allow_codex_runtime": False},
    }
    (task_dir / "task_state.json").write_text(json.dumps(state), encoding="utf-8")
    (task_dir / "artifacts.json").write_text(json.dumps({"task_id": "task", "artifacts": []}), encoding="utf-8")
    (task_dir / "pipeline_trace.json").write_text(json.dumps({"task_id": "task", "events": []}), encoding="utf-8")
    return task_dir
