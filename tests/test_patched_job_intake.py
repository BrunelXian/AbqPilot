import json
from pathlib import Path

from abqpilot.patching.patched_job_intake import intake_patched_job_output, poll_patched_job_status


def test_status_poll_maps_queued_to_waiting(monkeypatch, tmp_path):
    workflow = _workflow(tmp_path)
    _patch_adapter(monkeypatch, "QUEUED", odb_exists=False)

    result = poll_patched_job_status(workflow)

    assert result["details"]["normalized_status"] == "JOB_QUEUED"
    assert result["details"]["final_status"] == "WAITING_FOR_PATCHED_JOB"
    assert result["details"]["opened_odb"] is False


def test_status_poll_maps_running_to_waiting(monkeypatch, tmp_path):
    workflow = _workflow(tmp_path)
    _patch_adapter(monkeypatch, "RUNNING", odb_exists=False)

    result = poll_patched_job_status(workflow)

    assert result["details"]["final_status"] == "WAITING_FOR_PATCHED_JOB"


def test_status_poll_failed_maps_to_patched_failed(monkeypatch, tmp_path):
    workflow = _workflow(tmp_path)
    _patch_adapter(monkeypatch, "FAILED", odb_exists=False)

    result = poll_patched_job_status(workflow)

    assert result["details"]["final_status"] == "PATCHED_JOB_FAILED"


def test_status_poll_completed_missing_odb_waits_for_outputs(monkeypatch, tmp_path):
    workflow = _workflow(tmp_path)
    _patch_adapter(monkeypatch, "COMPLETED", odb_exists=False)

    result = poll_patched_job_status(workflow)

    assert result["details"]["normalized_status"] == "JOB_ODB_MISSING"
    assert result["details"]["final_status"] == "WAITING_FOR_PATCHED_JOB_OUTPUTS"


def test_status_poll_completed_with_odb_outputs_ready(monkeypatch, tmp_path):
    workflow = _workflow(tmp_path)
    _patch_adapter(monkeypatch, "COMPLETED", odb_exists=True)

    result = poll_patched_job_status(workflow)

    assert result["details"]["normalized_status"] == "JOB_OUTPUTS_READY"
    assert result["details"]["final_status"] == "JOB_OUTPUTS_READY"


def test_intake_blocks_if_queued_and_no_manual_odb(tmp_path):
    workflow = _workflow(tmp_path, normalized="JOB_QUEUED")

    result = intake_patched_job_output(workflow)

    assert result["verdict"] == "WAITING_FOR_PATCHED_JOB"
    assert result["details"]["output_accepted"] is False
    assert result["details"]["opened_odb"] is False


def test_intake_accepts_valid_manual_odb_without_opening(tmp_path):
    workflow = _workflow(tmp_path, normalized="JOB_QUEUED")
    odb = tmp_path / "manual.odb"
    odb.write_text("fixture", encoding="utf-8")

    result = intake_patched_job_output(workflow, manual_odb_path=odb)

    assert result["verdict"] == "PATCHED_JOB_OUTPUT_ACCEPTED"
    assert result["details"]["accepted_odb_path"] == str(odb)
    assert result["details"]["opened_odb"] is False


def test_intake_rejects_missing_manual_odb(tmp_path):
    workflow = _workflow(tmp_path)

    result = intake_patched_job_output(workflow, manual_odb_path=tmp_path / "missing.odb")

    assert result["verdict"] == "PATCHED_JOB_OUTPUT_REJECTED_MISSING"


def test_intake_rejects_locked_odb(tmp_path):
    workflow = _workflow(tmp_path)
    odb = tmp_path / "locked.odb"
    odb.write_text("fixture", encoding="utf-8")
    odb.with_suffix(".lck").write_text("locked", encoding="utf-8")

    result = intake_patched_job_output(workflow, manual_odb_path=odb)

    assert result["verdict"] == "PATCHED_JOB_OUTPUT_REJECTED_LOCKED"


def test_intake_rejects_non_odb_path(tmp_path):
    workflow = _workflow(tmp_path)
    text = tmp_path / "not_odb.txt"
    text.write_text("fixture", encoding="utf-8")

    result = intake_patched_job_output(workflow, manual_odb_path=text)

    assert result["verdict"] == "PATCHED_JOB_OUTPUT_REJECTED_INVALID_PATH"


def _workflow(tmp_path, normalized="JOB_QUEUED"):
    workflow = tmp_path / "task" / "patch_queue_workflows" / "queue_001"
    workflow.mkdir(parents=True)
    (workflow / "patch_candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_inp_path": str(tmp_path / "candidate.inp"),
                "candidate_inp_sha256": "abc",
                "patch_type": "heat_flux_magnitude_adjustment",
            }
        ),
        encoding="utf-8",
    )
    (workflow / "patch_jobpilot_real_enqueue_result.json").write_text(json.dumps({"job_id": "q_patch"}), encoding="utf-8")
    (workflow / "patch_jobpilot_real_enqueue_request.json").write_text(
        json.dumps({"job_name": "candidate", "inp_path": str(tmp_path / "candidate.inp")}),
        encoding="utf-8",
    )
    (workflow / "patch_queue_status_summary.json").write_text(
        json.dumps(
            {
                "job_id": "q_patch",
                "raw_status": "QUEUED",
                "normalized_status": normalized,
                "expected_odb_path": str(tmp_path / "candidate.odb"),
                "odb_exists": False,
                "lock_exists": False,
                "opened_odb": False,
                "submitted_solver": False,
                "queue_runner_launched": False,
            }
        ),
        encoding="utf-8",
    )
    return workflow


def _patch_adapter(monkeypatch, raw_status, odb_exists):
    class FakeAdapter:
        def __init__(self, project_root=None):
            self.project_root = project_root

        def poll_status(self, job_id=None, inp_path=None):
            return {"status": raw_status, "job_id": job_id, "inp_path": inp_path, "errors": [], "warnings": []}

        def locate_outputs(self, job_id=None, inp_path=None):
            return {
                "job_id": job_id,
                "inp_path": inp_path,
                "expected_odb_path": str(Path(inp_path or "candidate.inp").with_suffix(".odb")),
                "odb_exists": odb_exists,
                "lock_exists": False,
                "errors": [],
                "warnings": [],
            }

    monkeypatch.setattr("abqpilot.patching.patch_queue_workflow.AbqJobPilotPreflightAdapter", FakeAdapter)
