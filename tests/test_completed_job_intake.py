import json
from pathlib import Path

from abqpilot import cli
from abqpilot.core.completed_job_intake import continue_from_job_output


def test_completed_job_intake_waits_for_queued_job(tmp_path):
    task_dir = _write_task(tmp_path, "JOB_QUEUED", odb_exists=False)

    result = continue_from_job_output(task_dir)

    assert result["verdict"] == "WAITING_FOR_ABQJOBPILOT"
    assert result["success"] is True
    assert result["details"]["continue_to_solver_intake"] is False
    state = json.loads((task_dir / "task_state.json").read_text(encoding="utf-8"))
    assert state["status"] == "WAITING_FOR_ABQJOBPILOT"
    assert state["requires_human_action"] is False


def test_completed_job_intake_accepts_existing_manual_odb(tmp_path):
    task_dir = _write_task(tmp_path, "JOB_QUEUED", odb_exists=False)
    odb = tmp_path / "manual.odb"
    odb.write_bytes(b"placeholder odb")

    result = continue_from_job_output(task_dir, manual_odb_path=odb)

    assert result["verdict"] == "JOB_OUTPUTS_READY"
    assert result["details"]["accepted_odb_path"] == str(odb)
    assert result["details"]["continue_to_solver_intake"] is True
    assert result["details"]["opened_odb"] is False
    assert result["details"]["submitted_solver"] is False
    artifacts = json.loads((task_dir / "artifacts.json").read_text(encoding="utf-8"))
    assert any(item["name"] == "accepted_odb" for item in artifacts["artifacts"])


def test_completed_job_intake_rejects_missing_manual_odb(tmp_path):
    task_dir = _write_task(tmp_path, "JOB_QUEUED", odb_exists=False)

    result = continue_from_job_output(task_dir, manual_odb_path=tmp_path / "missing.odb")

    assert result["verdict"] == "MANUAL_ODB_MISSING"
    assert result["success"] is False
    assert "ODB does not exist" in result["errors"][0]


def test_completed_job_intake_rejects_locked_manual_odb(tmp_path):
    task_dir = _write_task(tmp_path, "JOB_QUEUED", odb_exists=False)
    odb = tmp_path / "manual.odb"
    odb.write_bytes(b"placeholder odb")
    odb.with_suffix(".lck").write_text("locked", encoding="utf-8")

    result = continue_from_job_output(task_dir, manual_odb_path=odb)

    assert result["verdict"] == "MANUAL_ODB_LOCKED"
    assert result["success"] is False


def test_completed_job_intake_handles_job_odb_missing(tmp_path):
    task_dir = _write_task(tmp_path, "JOB_ODB_MISSING", odb_exists=False)

    result = continue_from_job_output(task_dir)

    assert result["verdict"] == "WAITING_FOR_SOLVER_OUTPUTS"
    state = json.loads((task_dir / "task_state.json").read_text(encoding="utf-8"))
    assert state["status"] == "WAITING_FOR_SOLVER_OUTPUTS"
    assert state["requires_human_action"] is True


def test_completed_job_intake_cli_command(tmp_path):
    task_dir = _write_task(tmp_path, "JOB_OUTPUTS_READY", odb_exists=True)

    result = cli.command_continue_from_job_output(task_dir)

    assert result["verdict"] == "JOB_OUTPUTS_READY"
    assert Path(result["output_paths"]["stage2_8_completed_job_intake_summary_json"]).exists()


def _write_task(tmp_path, normalized_status, odb_exists):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    step_dir = task_dir / "steps" / "07_abqjobpilot_status_poll"
    step_dir.mkdir(parents=True)
    summary_path = step_dir / "abqjobpilot_status_summary.json"
    expected_odb = tmp_path / "case.odb"
    if odb_exists:
        expected_odb.write_bytes(b"placeholder odb")
    summary = {
        "task_id": "task",
        "job_id": "q_test",
        "raw_status": "COMPLETED" if normalized_status == "JOB_OUTPUTS_READY" else "QUEUED",
        "normalized_status": normalized_status,
        "expected_odb_path": str(expected_odb),
        "odb_exists": odb_exists,
        "lock_exists": False,
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    state = {
        "task_id": "task",
        "status": normalized_status,
        "current_step": "07_abqjobpilot_status_poll",
        "stop_reason": normalized_status,
        "requires_human_action": False,
        "human_action_reason": None,
        "steps": {},
        "completed_steps": [],
        "failed_steps": [],
        "skipped_steps": [],
    }
    (task_dir / "task_state.json").write_text(json.dumps(state), encoding="utf-8")
    artifacts = {
        "task_id": "task",
        "artifacts": [
            {
                "name": "abqjobpilot_status_summary",
                "kind": "generated",
                "path": str(summary_path),
                "exists": True,
                "producer_step": "07_abqjobpilot_status_poll",
            }
        ],
    }
    (task_dir / "artifacts.json").write_text(json.dumps(artifacts), encoding="utf-8")
    return task_dir
