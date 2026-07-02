import json
from pathlib import Path

from abqpilot.patching.patch_queue_workflow import (
    PATCH_QUEUE_APPROVAL_PHRASE,
    approve_patch_queue,
    poll_patch_queue,
    queue_patch_preview,
    validate_patch_preview_for_queue,
)


def test_invalid_preview_blocks(tmp_path):
    task = tmp_path / "task"
    task.mkdir()

    result = queue_patch_preview(task_dir=task, patch_preview_dir=task / "missing", mode="preflight-only")

    assert result["verdict"] == "PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW"
    assert result["details"]["solver_submitted"] is False


def test_preview_with_failed_guards_blocks(tmp_path):
    task, preview = _preview(tmp_path, static_status="FAIL")

    result = queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="preflight-only")

    assert result["verdict"] == "PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW"
    assert "static_validator_status check failed" in result["errors"]


def test_preview_with_failed_diff_guard_blocks(tmp_path):
    task, preview = _preview(tmp_path, diff_status="FAIL")

    result = queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="preflight-only")

    assert result["verdict"] == "PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW"
    assert "diff_guard_status check failed" in result["errors"]


def test_preview_with_failed_physics_guard_blocks(tmp_path):
    task, preview = _preview(tmp_path, physics_status="FAIL")

    result = queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="preflight-only")

    assert result["verdict"] == "PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW"
    assert "physics_guard_status check failed" in result["errors"]


def test_preview_with_unrelated_changes_blocks(tmp_path):
    task, preview = _preview(tmp_path, unrelated=1)

    validation = validate_patch_preview_for_queue(task, preview)

    assert validation["eligible"] is False
    assert "unrelated_changes_count check failed" in validation["errors"]


def test_missing_candidate_inp_blocks(tmp_path):
    task, preview = _preview(tmp_path)
    candidate = Path(json.loads((preview / "patch_preview_summary.json").read_text(encoding="utf-8"))["candidate_inp_path"])
    candidate.unlink()

    validation = validate_patch_preview_for_queue(task, preview)

    assert validation["eligible"] is False
    assert "candidate_inp_exists check failed" in validation["errors"]


def test_preflight_only_runs_no_dry_run_or_real_enqueue(monkeypatch, tmp_path):
    task, preview = _preview(tmp_path)
    calls = {"preflight": 0, "dry": 0, "real": 0}
    _patch_adapter(monkeypatch, calls)

    result = queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="preflight-only")

    assert result["verdict"] == "PATCH_QUEUE_PREFLIGHT_READY"
    assert calls == {"preflight": 1, "dry": 0, "real": 0}
    workflow = Path(result["output_paths"]["artifact_dir"])
    assert (workflow / "patch_jobpilot_preflight_result.json").exists()
    assert not (workflow / "patch_jobpilot_dry_run_result.json").exists()


def test_dry_run_mode_creates_candidate_approval_request(monkeypatch, tmp_path):
    task, preview = _preview(tmp_path)
    calls = {"preflight": 0, "dry": 0, "real": 0}
    _patch_adapter(monkeypatch, calls, dry_queue_only=True)

    result = queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="dry-run-enqueue")

    assert result["verdict"] == "PATCH_QUEUE_DRY_RUN_READY"
    assert result["details"]["approval_status"] == "APPROVAL_REQUIRED"
    assert result["details"]["real_enqueue_status"] == "NOT_RUN"
    assert calls == {"preflight": 1, "dry": 1, "real": 0}
    workflow = Path(result["output_paths"]["artifact_dir"])
    request = json.loads((workflow / "patch_candidate_approval_request.json").read_text(encoding="utf-8"))
    assert request["candidate_inp_sha256"]
    assert request["unrelated_changes_count"] == 0


def test_real_queue_only_requires_approval_token(monkeypatch, tmp_path):
    workflow = _dry_run_workflow(monkeypatch, tmp_path)

    result = queue_patch_preview(workflow_dir=workflow, mode="real-queue-only")

    assert result["verdict"] == "PATCH_QUEUE_REAL_ENQUEUE_BLOCKED"
    assert result["details"]["approval_status"] == "APPROVAL_TOKEN_MISSING"


def test_wrong_approval_phrase_rejected(monkeypatch, tmp_path):
    workflow = _dry_run_workflow(monkeypatch, tmp_path)

    result = approve_patch_queue(workflow, "human", "wrong", expires_hours=24)

    assert result["status"] == "APPROVAL_TOKEN_INVALID"


def test_token_hash_mismatch_rejected(monkeypatch, tmp_path):
    workflow = _dry_run_workflow(monkeypatch, tmp_path)
    token = approve_patch_queue(workflow, "human", PATCH_QUEUE_APPROVAL_PHRASE, expires_hours=24)
    token_path = Path(token["approval_token_path"])
    payload = json.loads(token_path.read_text(encoding="utf-8"))
    payload["candidate_inp_sha256"] = "bad"
    token_path.write_text(json.dumps(payload), encoding="utf-8")

    result = queue_patch_preview(workflow_dir=workflow, mode="real-queue-only", approval_token=token_path)

    assert result["details"]["approval_status"] == "APPROVAL_HASH_MISMATCH"


def test_valid_token_allows_mocked_real_queue_enqueue(monkeypatch, tmp_path):
    workflow = _dry_run_workflow(monkeypatch, tmp_path)
    token = approve_patch_queue(workflow, "human", PATCH_QUEUE_APPROVAL_PHRASE, expires_hours=24)

    result = queue_patch_preview(workflow_dir=workflow, mode="real-queue-only", approval_token=token["approval_token_path"])

    assert result["verdict"] == "PATCH_QUEUE_REAL_ENQUEUE_COMPLETED"
    assert result["details"]["real_enqueue_status"] == "REAL_ENQUEUE_COMPLETED"
    assert result["details"]["final_pipeline_status"] == "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER"
    assert result["details"]["solver_submitted"] is False
    assert (workflow / "patch_jobpilot_real_enqueue_result.json").exists()


def test_status_poll_maps_queued_without_opening_odb(monkeypatch, tmp_path):
    workflow = _dry_run_workflow(monkeypatch, tmp_path)
    token = approve_patch_queue(workflow, "human", PATCH_QUEUE_APPROVAL_PHRASE, expires_hours=24)
    queue_patch_preview(workflow_dir=workflow, mode="real-queue-only", approval_token=token["approval_token_path"])

    result = poll_patch_queue(workflow)

    assert result["verdict"] == "JOB_QUEUED"
    assert result["details"]["opened_odb"] is False
    assert (workflow / "patch_queue_status_summary.json").exists()


def _dry_run_workflow(monkeypatch, tmp_path):
    task, preview = _preview(tmp_path)
    _patch_adapter(monkeypatch, {"preflight": 0, "dry": 0, "real": 0}, dry_queue_only=True)
    result = queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="dry-run-enqueue")
    return Path(result["output_paths"]["artifact_dir"])


def _patch_adapter(monkeypatch, calls, dry_queue_only=True):
    class FakeAdapter:
        def __init__(self, project_root=None):
            self.project_root = project_root

        def build_request(self, inp_path, job_name, cpus, batch, strategy, working_dir=None, metadata=None):
            return {
                "inp_path": str(inp_path),
                "job_name": job_name,
                "cpus": cpus,
                "batch": batch,
                "strategy": strategy,
                "working_dir": working_dir,
                "submission_mode": "preview_only",
                "allow_solver_submit": False,
                "metadata": metadata or {},
            }

        def preflight(self, request):
            calls["preflight"] += 1
            return {"status": "PREVIEW_READY", "job_id": request["job_name"], "command_preview": "preview", "errors": [], "warnings": []}

        def dry_run_enqueue(self, request):
            calls["dry"] += 1
            return {
                "status": "DRY_RUN_READY",
                "job_id": request["job_name"],
                "runtime_mutation_detected": False,
                "queue_only": dry_queue_only,
                "errors": [],
                "warnings": [],
            }

        def real_enqueue(self, request, approval_report):
            calls["real"] += 1
            assert approval_report["approval_token_status"] == "APPROVAL_TOKEN_VALID"
            return {
                "status": "REAL_ENQUEUE_COMPLETED",
                "job_id": "q_patch",
                "queue_mutated": True,
                "forbidden_mutation_detected": False,
                "solver_started": False,
                "runner_started": False,
                "gui_required": False,
                "errors": [],
                "warnings": [],
            }

        def poll_status(self, job_id=None, inp_path=None):
            return {"status": "QUEUED", "job_id": job_id, "inp_path": inp_path, "errors": [], "warnings": []}

        def locate_outputs(self, job_id=None, inp_path=None):
            return {"job_id": job_id, "inp_path": inp_path, "odb_exists": False, "lock_exists": False, "errors": [], "warnings": []}

    monkeypatch.setattr("abqpilot.patching.patch_queue_workflow.AbqJobPilotPreflightAdapter", FakeAdapter)


def _preview(tmp_path, static_status="PASS", diff_status="PASS", physics_status="PASS", unrelated=0):
    task = tmp_path / "task"
    preview = task / "patch_previews" / "preview_001"
    preview.mkdir(parents=True)
    source = tmp_path / "source.inp"
    candidate = tmp_path / "candidate.inp"
    source.write_text("*Heading\n", encoding="utf-8")
    candidate.write_text("*Heading\n** patched\n", encoding="utf-8")
    summary = {
        "schema_version": "0.1",
        "task_id": task.name,
        "proposal_verdict": "PATCH_PROPOSED",
        "patch_type": "heat_flux_magnitude_adjustment",
        "preview_status": "PATCH_PREVIEW_READY",
        "source_inp_path": str(source),
        "candidate_inp_path": str(candidate),
        "changed_lines_count": 1,
        "unrelated_changes_count": unrelated,
        "static_validator_status": static_status,
        "diff_guard_status": diff_status,
        "physics_guard_status": physics_status,
        "solver_submitted": False,
        "job_enqueued": False,
        "requires_human_review": True,
    }
    (preview / "patch_preview_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return task, preview
