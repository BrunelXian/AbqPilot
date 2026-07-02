import json
from pathlib import Path

from abqpilot.ui_state.event_stream import build_event_stream
from abqpilot.ui_state.module_registry import build_module_registry
from abqpilot.ui_state.view_model import build_task_view_model


def test_module_registry_contains_major_modules():
    modules = build_module_registry()
    names = {module["display_name"] for module in modules}

    assert "CAE Export" in names
    assert "Status Poll" in names
    assert "ODB Metrics" in names
    assert "Evaluation" in names
    assert "Repair Plan" in names
    assert "GUI" in names


def test_event_stream_builds_from_task_artifacts(tmp_path):
    task_dir = _write_view_task(tmp_path)

    events = build_event_stream(task_dir)

    assert events
    assert any(event["title"] == "STEP_COMPLETED" for event in events)
    assert all("module_id" in event for event in events)


def test_view_model_identifies_current_module_and_right_panel(tmp_path):
    task_dir = _write_view_task(tmp_path)

    model = build_task_view_model(task_dir)

    assert model["task_id"] == "task"
    assert model["current_module"] == "status_poll"
    assert model["right_panel"]["module_name"] == "Status Poll"
    assert model["right_panel"]["status"] == "WAITING_FOR_ABQJOBPILOT"
    assert "q_test" in model["right_panel"]["input_summary"]
    assert model["right_panel"]["active_artifacts"]


def _write_view_task(tmp_path):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    step_dir = task_dir / "steps" / "07_abqjobpilot_status_poll"
    step_dir.mkdir(parents=True)
    state = {
        "task_id": "task",
        "status": "WAITING_FOR_ABQJOBPILOT",
        "current_step": "07_abqjobpilot_status_poll",
        "stop_reason": "WAITING_FOR_ABQJOBPILOT",
        "steps": {
            "07_abqjobpilot_status_poll": {"status": "COMPLETED", "verdict": "JOB_QUEUED"},
        },
        "completed_steps": ["07_abqjobpilot_status_poll"],
        "failed_steps": [],
        "skipped_steps": [],
        "requires_human_action": False,
        "human_action_reason": None,
    }
    (task_dir / "task_state.json").write_text(json.dumps(state), encoding="utf-8")
    status_summary = step_dir / "abqjobpilot_status_summary.json"
    status_summary.write_text(
        json.dumps(
            {
                "job_id": "q_test",
                "raw_status": "QUEUED",
                "normalized_status": "JOB_QUEUED",
                "expected_odb_path": str(tmp_path / "case.odb"),
                "odb_exists": False,
                "lock_exists": False,
            }
        ),
        encoding="utf-8",
    )
    real_enqueue = task_dir / "steps" / "06_abqjobpilot_real_enqueue" / "abqjobpilot_real_enqueue_result.json"
    real_enqueue.parent.mkdir(parents=True)
    real_enqueue.write_text(json.dumps({"status": "REAL_ENQUEUE_COMPLETED", "job_id": "q_test"}), encoding="utf-8")
    (task_dir / "artifacts.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "artifacts": [
                    {
                        "name": "abqjobpilot_status_summary",
                        "kind": "generated",
                        "path": str(status_summary),
                        "exists": True,
                        "producer_step": "07_abqjobpilot_status_poll",
                    },
                    {
                        "name": "abqjobpilot_real_enqueue_result",
                        "kind": "generated",
                        "path": str(real_enqueue),
                        "exists": True,
                        "producer_step": "06_abqjobpilot_real_enqueue",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "pipeline_trace.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "events": [
                    {
                        "timestamp": "2026-01-01T00:00:00",
                        "event": "STEP_COMPLETED",
                        "step": "07_abqjobpilot_status_poll",
                        "verdict": "JOB_QUEUED",
                        "reason": None,
                        "result_path": str(step_dir / "step_result.json"),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (step_dir / "step_result.json").write_text(
        json.dumps({"command": "07_abqjobpilot_status_poll", "verdict": "JOB_QUEUED", "success": True}),
        encoding="utf-8",
    )
    return task_dir
