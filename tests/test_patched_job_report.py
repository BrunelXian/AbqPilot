import json

from abqpilot.patching.patched_job_report import report_patched_job


def test_report_handles_missing_metrics(tmp_path):
    workflow = _workflow(tmp_path, normalized="JOB_QUEUED", output_accepted=False)

    result = report_patched_job(workflow)

    assert result["verdict"] == "PATCHED_JOB_WAITING"
    assert result["details"]["submitted_solver"] is False
    assert result["details"]["queue_runner_launched"] is False
    assert result["details"]["opened_odb_directly"] is False
    assert (workflow / "patched_job_report.json").exists()


def test_report_handles_metrics_only_insufficient_reference(tmp_path):
    workflow = _workflow(tmp_path, normalized="JOB_OUTPUTS_READY", output_accepted=True)
    metrics_path = workflow / "patched_job_metrics" / "odb_metrics_pair.json"
    metrics_path.parent.mkdir()
    metrics_path.write_text(json.dumps({"cases": [{"role": "power_x2", "metrics": {"NT_max": 10.0}}]}), encoding="utf-8")
    (workflow / "patched_job_metrics_summary.json").write_text(
        json.dumps({"metrics_available": True, "metrics_json_path": str(metrics_path), "verdict": "PATCHED_JOB_METRICS_READY"}),
        encoding="utf-8",
    )

    result = report_patched_job(workflow)

    assert result["verdict"] == "INSUFFICIENT_REFERENCE"
    assert result["details"]["patched_metrics_available"] is True
    assert result["details"]["reference_metrics_available"] is False


def _workflow(tmp_path, normalized, output_accepted):
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    (workflow / "patch_candidate_manifest.json").write_text(
        json.dumps({"patch_type": "heat_flux_magnitude_adjustment", "candidate_inp_sha256": "abc"}),
        encoding="utf-8",
    )
    (workflow / "patch_queue_status_summary.json").write_text(
        json.dumps({"job_id": "q_patch", "normalized_status": normalized, "errors": [], "warnings": []}),
        encoding="utf-8",
    )
    (workflow / "patched_job_output_intake_summary.json").write_text(
        json.dumps({"output_accepted": output_accepted, "accepted_odb_path": None, "errors": [], "warnings": []}),
        encoding="utf-8",
    )
    return workflow
