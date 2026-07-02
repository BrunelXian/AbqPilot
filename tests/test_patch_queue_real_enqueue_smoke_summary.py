import json

from abqpilot.patching.patch_queue_smoke import write_stage3_8a_smoke_summary


def test_stage3_8a_smoke_summary_writer(tmp_path):
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    before = _runtime_snapshot(queue_size=2, live_size=3, reports_size=4)
    after = _runtime_snapshot(queue_size=20, live_size=3, reports_size=4)
    _write(workflow / "patch_candidate_manifest.json", {"patch_preview_dir": "preview", "candidate_inp_path": "candidate.inp", "candidate_inp_sha256": "abc", "source_inp_path": "source.inp", "source_inp_sha256": "def", "patch_type": "heat_flux_magnitude_adjustment"})
    _write(workflow / "patch_queue_summary.json", {"approval_status": "APPROVAL_TOKEN_VALID", "job_id": "q_patch", "final_pipeline_status": "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER"})
    _write(workflow / "patch_jobpilot_preflight_result.json", {"status": "PREVIEW_READY"})
    _write(workflow / "patch_jobpilot_dry_run_result.json", {"status": "DRY_RUN_READY"})
    _write(workflow / "patch_candidate_approval_request.json", {"status": "APPROVAL_REQUIRED"})
    _write(
        workflow / "patch_jobpilot_real_enqueue_result.json",
        {
            "status": "REAL_ENQUEUE_COMPLETED",
            "job_id": "q_patch",
            "queue_only": True,
            "queue_file_mutated": True,
            "solver_started": False,
            "runner_started": False,
            "gui_required": False,
            "forbidden_mutation_detected": False,
            "runtime_snapshot_before": before,
            "runtime_snapshot_after": after,
            "solver_output_snapshot_before": {"files": {".odb": {"exists": False}}},
            "solver_output_snapshot_after": {"files": {".odb": {"exists": False}}},
        },
    )
    _write(workflow / "patch_queue_status_summary.json", {"normalized_status": "JOB_QUEUED"})

    result = write_stage3_8a_smoke_summary(workflow)

    assert result["success"] is True
    summary = json.loads((workflow / "stage3_8a_patch_queue_real_enqueue_smoke_summary.json").read_text(encoding="utf-8"))
    assert summary["solver_submitted"] is False
    assert summary["queue_runner_launched"] is False
    assert summary["opened_odb"] is False
    assert "sk-" not in json.dumps(summary)


def _runtime_snapshot(queue_size, live_size, reports_size):
    return {
        "paths": {
            "runtime\\queue.json": {"path": "D:\\Projects\\abqjobpilot_dev\\runtime\\queue.json", "exists": True, "size": queue_size, "mtime_ns": queue_size},
            "runtime\\live_status.json": {"path": "D:\\Projects\\abqjobpilot_dev\\runtime\\live_status.json", "exists": True, "size": live_size, "mtime_ns": live_size},
            "runtime\\reports": {"path": "D:\\Projects\\abqjobpilot_dev\\runtime\\reports", "exists": True, "is_dir": True, "size": reports_size, "mtime_ns": reports_size},
        }
    }


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
