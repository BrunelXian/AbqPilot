import json
from pathlib import Path

from abqpilot import cli
from abqpilot.reporting.alpha_freeze import export_alpha_freeze
from abqpilot.reporting.run_report import export_run_report


def test_run_report_export_writes_json_and_markdown(tmp_path):
    task_dir = _write_report_task(tmp_path)

    result = export_run_report(task_dir)

    assert result["verdict"] == "RUN_REPORT_EXPORTED"
    assert Path(result["output_paths"]["run_report_json"]).exists()
    assert Path(result["output_paths"]["run_report_md"]).exists()
    report = json.loads(Path(result["output_paths"]["run_report_json"]).read_text(encoding="utf-8"))
    assert report["task_id"] == "task"
    assert report["safety_boundary_summary"]["abaqus_solver_submit"] == "not automatic"


def test_export_run_report_cli_command(tmp_path):
    task_dir = _write_report_task(tmp_path)

    result = cli.command_export_run_report(task_dir)

    assert result["success"] is True
    assert Path(result["output_paths"]["run_report_md"]).exists()


def test_alpha_freeze_report_writes_capability_and_safety_matrices(tmp_path):
    result = export_alpha_freeze(root=tmp_path, test_results="1 passed")

    assert result["verdict"] == "PASS_ABQPILOT_V2_MEGA_SPRINT_01_GUI_AND_CONTINUATION_ALPHA_READY"
    freeze_dir = Path(result["output_paths"]["alpha_freeze_dir"])
    assert (freeze_dir / "capability_matrix.md").exists()
    assert (freeze_dir / "safety_boundary_matrix.md").exists()
    assert "GUI alpha" in (freeze_dir / "capability_matrix.md").read_text(encoding="utf-8")
    assert "OpenAI API" in (freeze_dir / "safety_boundary_matrix.md").read_text(encoding="utf-8")


def _write_report_task(tmp_path):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    task_dir.mkdir(parents=True)
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
    status = task_dir / "status.json"
    status.write_text(json.dumps({"job_id": "q_test", "normalized_status": "JOB_QUEUED"}), encoding="utf-8")
    real_enqueue = task_dir / "real_enqueue.json"
    real_enqueue.write_text(
        json.dumps(
            {
                "status": "REAL_ENQUEUE_COMPLETED",
                "queue_only": True,
                "solver_started": False,
                "runner_started": False,
                "gui_required": False,
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "artifacts.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "artifacts": [
                    {"name": "abqjobpilot_status_summary", "path": str(status), "kind": "generated", "exists": True},
                    {"name": "abqjobpilot_real_enqueue_result", "path": str(real_enqueue), "kind": "generated", "exists": True},
                ],
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "pipeline_trace.json").write_text(json.dumps({"task_id": "task", "events": []}), encoding="utf-8")
    return task_dir
