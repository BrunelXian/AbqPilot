from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file
from abqpilot.core.task_config import load_task_config
from abqpilot.integrations import AbqJobPilotPreflightAdapter, normalize_jobpilot_status
from abqpilot.patching.patch_queue_artifacts import (
    render_patch_approval_request,
    render_patch_queue_summary,
    write_json_artifact,
    write_text_artifact,
)


PATCH_QUEUE_APPROVAL_PHRASE = "I_APPROVE_ABQPILOT_PATCH_CANDIDATE_QUEUE_ONLY_ENQUEUE"
PATCH_QUEUE_APPROVAL_TYPE = "abqpilot_patch_candidate_queue_only_enqueue"
PATCH_QUEUE_SCHEMA_VERSION = "0.1"
VALID_MODES = {"preflight-only", "dry-run-enqueue", "real-queue-only"}


def queue_patch_preview(
    task_dir: str | Path | None = None,
    patch_preview_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
    mode: str = "preflight-only",
    workflow_dir: str | Path | None = None,
    approval_token: str | Path | None = None,
    abqjobpilot_root: str | Path | None = None,
    cpus: int | None = None,
    batch: str | None = None,
    strategy: str | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    if mode not in VALID_MODES:
        return _blocked_result("PATCH_TO_QUEUE_BLOCKED_INVALID_MODE", workflow_dir, [f"unsupported mode: {mode}"])

    if workflow_dir is not None:
        workflow = Path(workflow_dir)
        workflow.mkdir(parents=True, exist_ok=True)
        task = Path(task_dir) if task_dir is not None else _read_existing_task_dir(workflow)
        preview_dir = Path(patch_preview_dir) if patch_preview_dir is not None else _read_manifest_preview_dir(workflow)
    else:
        if task_dir is None:
            return _blocked_result("PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW", None, ["--task-dir is required"])
        task = Path(task_dir)
        preview_dir = Path(patch_preview_dir) if patch_preview_dir is not None else find_latest_ready_patch_preview(task)
        workflow = task / "patch_queue_workflows" / ("queue_" + _timestamp())
        workflow.mkdir(parents=True, exist_ok=True)

    config = _load_config(task, config_path)
    root = str(abqjobpilot_root or config.get("abqjobpilot", {}).get("project_root") or "")
    adapter = AbqJobPilotPreflightAdapter(project_root=root or None)

    preview_validation = validate_patch_preview_for_queue(
        task,
        preview_dir=preview_dir,
        candidate_inp=candidate_inp,
    )
    manifest = preview_validation.get("manifest", {})
    if not preview_validation["eligible"]:
        summary = _summary(
            workflow,
            task,
            manifest,
            workflow_status="PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW",
            errors=preview_validation["errors"],
        )
        _write_workflow_basics(workflow, mode, task, preview_dir, manifest, summary)
        return _workflow_result(summary, workflow, False)

    _write_workflow_basics(workflow, mode, task, preview_dir, manifest, None)

    request = adapter.build_request(
        inp_path=manifest["candidate_inp_path"],
        job_name=Path(manifest["candidate_inp_path"]).stem,
        cpus=int(cpus or config.get("abqjobpilot", {}).get("cpus") or config.get("jobpilot", {}).get("cpus") or 14),
        batch=batch or config.get("abqjobpilot", {}).get("batch") or config.get("jobpilot", {}).get("batch"),
        strategy=strategy or config.get("abqjobpilot", {}).get("strategy") or config.get("jobpilot", {}).get("strategy"),
        working_dir=str(Path(manifest["candidate_inp_path"]).parent),
        metadata={
            "source": "AbqPilot-v2",
            "stage": "3.8_patch_to_queue",
            "parent_task_id": task.name,
            "patch_preview_dir": str(preview_dir),
            "patch_type": manifest.get("patch_type"),
        },
    )
    request["submission_mode"] = "preview_only"
    request["allow_solver_submit"] = False

    preflight_result = _run_or_load_preflight(adapter, request, workflow, mode)
    if mode == "preflight-only":
        summary = _summary(
            workflow,
            task,
            manifest,
            workflow_status=_status_or_block(preflight_result, "PATCH_QUEUE_PREFLIGHT_READY"),
            request=request,
            preflight_result=preflight_result,
        )
        _write_summary(workflow, summary)
        return _workflow_result(summary, workflow, preflight_result.get("status") == "PREVIEW_READY")

    dry_run_result = _run_or_load_dry_run(adapter, request, workflow, mode)
    approval_request = create_patch_queue_approval_request(workflow, task, manifest)
    write_json_artifact(workflow / "patch_candidate_approval_request.json", approval_request)
    write_text_artifact(workflow / "patch_candidate_approval_request.md", render_patch_approval_request(approval_request))

    if mode == "dry-run-enqueue":
        ok = preflight_result.get("status") == "PREVIEW_READY" and dry_run_result.get("status") == "DRY_RUN_READY"
        summary = _summary(
            workflow,
            task,
            manifest,
            workflow_status="PATCH_QUEUE_DRY_RUN_READY" if ok else "PATCH_QUEUE_DRY_RUN_BLOCKED",
            request=request,
            preflight_result=preflight_result,
            dry_run_result=dry_run_result,
            approval_status="APPROVAL_REQUIRED",
        )
        _write_summary(workflow, summary)
        return _workflow_result(summary, workflow, ok)

    validation = validate_patch_queue_approval_token(workflow, approval_token)
    if validation["status"] != "APPROVAL_TOKEN_VALID":
        summary = _summary(
            workflow,
            task,
            manifest,
            workflow_status="PATCH_QUEUE_REAL_ENQUEUE_BLOCKED",
            request=request,
            preflight_result=preflight_result,
            dry_run_result=dry_run_result,
            approval_status=validation["status"],
            errors=validation.get("errors", []),
        )
        _write_summary(workflow, summary)
        return _workflow_result(summary, workflow, False)

    approval_report = _real_enqueue_approval_report(approval_request, validation, preflight_result, dry_run_result)
    real_result = adapter.real_enqueue(request, approval_report)
    _write_patch_real_enqueue_artifacts(workflow, request, real_result)
    ok = real_result.get("status") == "REAL_ENQUEUE_COMPLETED" and not real_result.get("forbidden_mutation_detected")
    summary = _summary(
        workflow,
        task,
        manifest,
        workflow_status="PATCH_QUEUE_REAL_ENQUEUE_COMPLETED" if ok else "PATCH_QUEUE_REAL_ENQUEUE_BLOCKED",
        request=request,
        preflight_result=preflight_result,
        dry_run_result=dry_run_result,
        approval_status=validation["status"],
        real_enqueue_result=real_result,
    )
    _write_summary(workflow, summary)
    return _workflow_result(summary, workflow, ok)


def approve_patch_queue(
    workflow_dir: str | Path,
    approved_by: str,
    approval_phrase: str,
    expires_hours: int | float = 24,
) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    request_path = workflow / "patch_candidate_approval_request.json"
    if approval_phrase != PATCH_QUEUE_APPROVAL_PHRASE:
        return _approval_result("APPROVAL_TOKEN_INVALID", workflow, False, ["approval phrase does not match required phrase"])
    if not request_path.exists():
        return _approval_result("APPROVAL_TOKEN_MISSING", workflow, False, ["patch candidate approval request is missing"])
    request = _read_json(request_path)
    safe, errors = patch_queue_request_conditions_are_safe(request)
    if not safe:
        return _approval_result("APPROVAL_UNSAFE_CONDITIONS", workflow, False, errors)
    created_at = datetime.now()
    token = {
        "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
        "approval_type": PATCH_QUEUE_APPROVAL_TYPE,
        "parent_task_id": request.get("parent_task_id"),
        "approved_step": "patch_candidate_real_queue_only_enqueue",
        "approved_by": approved_by,
        "approval_phrase": approval_phrase,
        "created_at": created_at.isoformat(timespec="seconds"),
        "expires_at": (created_at + timedelta(hours=float(expires_hours))).isoformat(timespec="seconds"),
        "patch_preview_dir": request.get("patch_preview_dir"),
        "candidate_inp_sha256": request.get("candidate_inp_sha256"),
        "job_request_sha256": request.get("job_request_sha256"),
        "preflight_result_sha256": request.get("preflight_result_sha256"),
        "dry_run_result_sha256": request.get("dry_run_result_sha256"),
        "patch_type": request.get("patch_type"),
        "changed_lines_count": request.get("changed_lines_count"),
        "unrelated_changes_count": request.get("unrelated_changes_count"),
        "conditions": request.get("required_conditions", {}),
    }
    path = workflow / "approvals" / "patch_queue_approval_token.json"
    write_json_artifact(path, token)
    return {
        "status": "APPROVAL_TOKEN_CREATED",
        "success": True,
        "approval_token_path": str(path),
        "token": token,
        "errors": [],
        "warnings": [],
    }


def validate_patch_queue_approval_token(workflow_dir: str | Path, token_path: str | Path | None = None) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    request_path = workflow / "patch_candidate_approval_request.json"
    token = Path(token_path) if token_path is not None else workflow / "approvals" / "patch_queue_approval_token.json"
    if not request_path.exists():
        return _validation_result("APPROVAL_TOKEN_MISSING", False, ["patch candidate approval request is missing"], token)
    request = _read_json(request_path)
    safe, errors = patch_queue_request_conditions_are_safe(request)
    if not safe:
        return _validation_result("APPROVAL_UNSAFE_CONDITIONS", False, errors, token)
    if not token.exists():
        return _validation_result("APPROVAL_TOKEN_MISSING", False, ["approval token is missing"], token)
    payload = _read_json(token)
    if payload.get("approval_type") != PATCH_QUEUE_APPROVAL_TYPE:
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["approval token type does not match"], token)
    if payload.get("approval_phrase") != PATCH_QUEUE_APPROVAL_PHRASE:
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["approval phrase is invalid"], token)
    if payload.get("parent_task_id") != request.get("parent_task_id"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["parent task id does not match"], token)
    try:
        expires_at = datetime.fromisoformat(str(payload.get("expires_at")))
    except ValueError:
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["approval token expires_at is invalid"], token)
    if expires_at <= datetime.now():
        return _validation_result("APPROVAL_TOKEN_EXPIRED", False, ["approval token is expired"], token)
    for field in (
        "patch_preview_dir",
        "candidate_inp_sha256",
        "job_request_sha256",
        "preflight_result_sha256",
        "dry_run_result_sha256",
        "patch_type",
        "changed_lines_count",
        "unrelated_changes_count",
    ):
        if payload.get(field) != request.get(field):
            return _validation_result("APPROVAL_HASH_MISMATCH", False, [f"approval token mismatch: {field}"], token)
    return _validation_result("APPROVAL_TOKEN_VALID", True, [], token)


def poll_patch_queue(workflow_dir: str | Path, abqjobpilot_root: str | Path | None = None) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    manifest = _read_json(workflow / "patch_candidate_manifest.json")
    real_result = _read_json(workflow / "patch_jobpilot_real_enqueue_result.json")
    request = _read_json(workflow / "patch_jobpilot_real_enqueue_request.json") or _read_json(workflow / "patch_jobpilot_preflight_request.json")
    root = str(abqjobpilot_root or real_result.get("project_root") or "")
    job_id = real_result.get("job_id") or request.get("job_name")
    if not job_id:
        summary = _poll_summary(workflow, manifest, {}, {}, "NEED_ABQJOBPILOT_JOB_ID")
        _write_poll_artifacts(workflow, {"job_id": None}, {}, summary)
        return _poll_result(summary, workflow, False)
    adapter = AbqJobPilotPreflightAdapter(project_root=root or None)
    status_result = adapter.poll_status(job_id=job_id, inp_path=request.get("inp_path"))
    output_result = adapter.locate_outputs(job_id=job_id, inp_path=request.get("inp_path"))
    normalized = normalize_jobpilot_status(status_result, output_result)
    summary = _poll_summary(workflow, manifest, status_result, output_result, normalized)
    _write_poll_artifacts(workflow, {"job_id": job_id, "inp_path": request.get("inp_path"), "read_only": True}, status_result, summary, output_result)
    return _poll_result(summary, workflow, True)


def validate_patch_preview_for_queue(
    task_dir: str | Path,
    preview_dir: str | Path | None,
    candidate_inp: str | Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if preview_dir is None:
        return {"eligible": False, "errors": ["patch preview directory was not found"], "manifest": {}}
    preview = Path(preview_dir)
    summary_path = preview / "patch_preview_summary.json"
    if not summary_path.exists():
        return {"eligible": False, "errors": [f"patch preview summary is missing: {summary_path}"], "manifest": {}}
    summary = _read_json(summary_path)
    candidate_path = Path(candidate_inp) if candidate_inp is not None else Path(str(summary.get("candidate_inp_path") or ""))
    source_path = Path(str(summary.get("source_inp_path") or ""))
    checks = {
        "preview_status": summary.get("preview_status") == "PATCH_PREVIEW_READY",
        "static_validator_status": summary.get("static_validator_status") == "PASS",
        "diff_guard_status": summary.get("diff_guard_status") == "PASS",
        "physics_guard_status": summary.get("physics_guard_status") == "PASS",
        "solver_submitted": summary.get("solver_submitted") is False,
        "job_enqueued": summary.get("job_enqueued") is False,
        "unrelated_changes_count": int(summary.get("unrelated_changes_count") or 0) == 0,
        "requires_human_review": summary.get("requires_human_review") is True,
        "candidate_inp_exists": candidate_path.exists() and candidate_path.suffix.lower() == ".inp",
        "source_inp_exists": source_path.exists() and source_path.suffix.lower() == ".inp",
    }
    for name, ok in checks.items():
        if not ok:
            errors.append(f"{name} check failed")
    manifest: dict[str, Any] = {
        "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
        "parent_task_id": Path(task_dir).name,
        "patch_preview_dir": str(preview),
        "candidate_inp_path": str(candidate_path) if candidate_path else None,
        "candidate_inp_sha256": sha256_file(candidate_path) if candidate_path.exists() else None,
        "source_inp_path": str(source_path) if source_path else None,
        "source_inp_sha256": sha256_file(source_path) if source_path.exists() else None,
        "patch_type": summary.get("patch_type"),
        "changed_lines_count": int(summary.get("changed_lines_count") or 0),
        "unrelated_changes_count": int(summary.get("unrelated_changes_count") or 0),
        "static_validator_status": summary.get("static_validator_status"),
        "diff_guard_status": summary.get("diff_guard_status"),
        "physics_guard_status": summary.get("physics_guard_status"),
        "eligible_for_preflight": not errors,
        "eligible_for_dry_run_enqueue": not errors,
        "eligible_for_real_enqueue": False,
        "requires_human_approval": True,
        "preview_summary_path": str(summary_path),
    }
    return {"eligible": not errors, "errors": errors, "manifest": manifest}


def find_latest_ready_patch_preview(task_dir: str | Path) -> Path | None:
    root = Path(task_dir) / "patch_previews"
    if not root.exists():
        return None
    candidates = [path for path in root.glob("preview_*") if (path / "patch_preview_summary.json").exists()]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def create_patch_queue_approval_request(workflow_dir: str | Path, task_dir: str | Path, manifest: dict[str, Any]) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    request_path = workflow / "patch_jobpilot_preflight_request.json"
    preflight_path = workflow / "patch_jobpilot_preflight_result.json"
    dry_run_path = workflow / "patch_jobpilot_dry_run_result.json"
    request = _read_json(request_path)
    preflight = _read_json(preflight_path)
    dry_run = _read_json(dry_run_path)
    return {
        "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
        "approval_type": PATCH_QUEUE_APPROVAL_TYPE,
        "parent_task_id": Path(task_dir).name,
        "patch_preview_dir": manifest.get("patch_preview_dir"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "APPROVAL_REQUIRED",
        "candidate_inp_path": manifest.get("candidate_inp_path"),
        "candidate_inp_sha256": manifest.get("candidate_inp_sha256"),
        "job_request_path": str(request_path),
        "job_request_sha256": sha256_file(request_path),
        "preflight_result_path": str(preflight_path),
        "preflight_result_sha256": sha256_file(preflight_path),
        "dry_run_result_path": str(dry_run_path),
        "dry_run_result_sha256": sha256_file(dry_run_path),
        "patch_type": manifest.get("patch_type"),
        "changed_lines_count": manifest.get("changed_lines_count"),
        "unrelated_changes_count": manifest.get("unrelated_changes_count"),
        "required_conditions": {
            "preflight_status": preflight.get("status"),
            "dry_run_enqueue_status": dry_run.get("status"),
            "runtime_mutation_detected": bool(dry_run.get("runtime_mutation_detected")),
            "allow_solver_submit": request.get("allow_solver_submit"),
            "submission_mode": request.get("submission_mode"),
            "static_validator_status": manifest.get("static_validator_status"),
            "diff_guard_status": manifest.get("diff_guard_status"),
            "physics_guard_status": manifest.get("physics_guard_status"),
            "unrelated_changes_count": manifest.get("unrelated_changes_count"),
        },
        "human_instructions": [
            "Review the candidate INP, patch preview guards, preflight result, and dry-run enqueue result.",
            "Only create an approval token if you intentionally authorize queue-only enqueue of this patch candidate.",
            "This approval request does not enqueue or submit a solver job.",
        ],
    }


def patch_queue_request_conditions_are_safe(request: dict[str, Any]) -> tuple[bool, list[str]]:
    conditions = request.get("required_conditions", {})
    errors: list[str] = []
    expected = {
        "preflight_status": "PREVIEW_READY",
        "dry_run_enqueue_status": "DRY_RUN_READY",
        "runtime_mutation_detected": False,
        "allow_solver_submit": False,
        "submission_mode": "preview_only",
        "static_validator_status": "PASS",
        "diff_guard_status": "PASS",
        "physics_guard_status": "PASS",
        "unrelated_changes_count": 0,
    }
    for key, value in expected.items():
        if conditions.get(key) != value:
            errors.append(f"{key} must be {value}")
    return not errors, errors


def _run_or_load_preflight(adapter: AbqJobPilotPreflightAdapter, request: dict[str, Any], workflow: Path, mode: str) -> dict[str, Any]:
    result_path = workflow / "patch_jobpilot_preflight_result.json"
    if mode == "real-queue-only" and result_path.exists():
        return _read_json(result_path)
    result = adapter.preflight(request)
    _write_patch_preflight_artifacts(workflow, request, result)
    return result


def _run_or_load_dry_run(adapter: AbqJobPilotPreflightAdapter, request: dict[str, Any], workflow: Path, mode: str) -> dict[str, Any]:
    result_path = workflow / "patch_jobpilot_dry_run_result.json"
    if mode == "real-queue-only" and result_path.exists():
        return _read_json(result_path)
    result = adapter.dry_run_enqueue(request)
    _write_patch_dry_run_artifacts(workflow, request, result)
    return result


def _write_patch_preflight_artifacts(workflow: Path, request: dict[str, Any], result: dict[str, Any]) -> None:
    write_json_artifact(workflow / "patch_jobpilot_preflight_request.json", request)
    write_json_artifact(workflow / "patch_jobpilot_preflight_result.json", result)
    write_text_artifact(
        workflow / "patch_jobpilot_command_preview.md",
        "# Patch Candidate JobPilot Preflight\n\n"
        f"Status: {result.get('status')}\n\n"
        "No job was enqueued. No solver was submitted.\n\n"
        "```powershell\n"
        f"{result.get('command_preview', '')}\n"
        "```\n",
    )


def _write_patch_dry_run_artifacts(workflow: Path, request: dict[str, Any], result: dict[str, Any]) -> None:
    safety = {
        "status": "ABQJOBPILOT_RUNTIME_MUTATION_DETECTED" if result.get("runtime_mutation_detected") else "DRY_RUN_RUNTIME_UNCHANGED",
        "runtime_mutation_detected": bool(result.get("runtime_mutation_detected")),
        "runtime_snapshot_before": result.get("runtime_snapshot_before"),
        "runtime_snapshot_after": result.get("runtime_snapshot_after"),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }
    write_json_artifact(workflow / "patch_jobpilot_dry_run_request.json", request)
    write_json_artifact(workflow / "patch_jobpilot_dry_run_result.json", result)
    write_json_artifact(workflow / "patch_jobpilot_dry_run_safety_report.json", safety)


def _write_patch_real_enqueue_artifacts(workflow: Path, request: dict[str, Any], result: dict[str, Any]) -> None:
    safety = {
        "status": result.get("status"),
        "queue_mutated": bool(result.get("queue_mutated")),
        "forbidden_mutation_detected": bool(result.get("forbidden_mutation_detected")),
        "runtime_mutation_report": result.get("runtime_mutation_report"),
        "runtime_snapshot_before": result.get("runtime_snapshot_before"),
        "runtime_snapshot_after": result.get("runtime_snapshot_after"),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
    }
    write_json_artifact(workflow / "patch_jobpilot_real_enqueue_request.json", request)
    write_json_artifact(workflow / "patch_jobpilot_real_enqueue_result.json", result)
    write_json_artifact(workflow / "patch_jobpilot_real_enqueue_safety_report.json", safety)


def _write_workflow_basics(
    workflow: Path,
    mode: str,
    task: Path,
    preview_dir: Path | None,
    manifest: dict[str, Any],
    summary: dict[str, Any] | None,
) -> None:
    request = {
        "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
        "mode": mode,
        "task_dir": str(task),
        "patch_preview_dir": str(preview_dir) if preview_dir else None,
        "solver_submitted": False,
        "queue_runner_launched": False,
        "opened_odb": False,
        "llm_executed_action": False,
    }
    write_json_artifact(workflow / "patch_queue_workflow_request.json", request)
    if manifest:
        write_json_artifact(workflow / "patch_candidate_manifest.json", manifest)
    if summary is not None:
        _write_summary(workflow, summary)


def _write_summary(workflow: Path, summary: dict[str, Any]) -> None:
    write_json_artifact(workflow / "patch_queue_summary.json", summary)
    write_text_artifact(workflow / "patch_queue_summary.md", render_patch_queue_summary(summary))
    write_json_artifact(
        workflow / "patch_queue_workflow_result.json",
        {
            "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
            "workflow_status": summary.get("workflow_status"),
            "success": summary.get("workflow_status")
            in {"PATCH_QUEUE_PREFLIGHT_READY", "PATCH_QUEUE_DRY_RUN_READY", "PATCH_QUEUE_REAL_ENQUEUE_COMPLETED"},
            "summary_path": str(workflow / "patch_queue_summary.json"),
            "solver_submitted": False,
            "queue_runner_launched": False,
            "opened_odb": False,
        },
    )


def _summary(
    workflow: Path,
    task: Path,
    manifest: dict[str, Any],
    workflow_status: str,
    request: dict[str, Any] | None = None,
    preflight_result: dict[str, Any] | None = None,
    dry_run_result: dict[str, Any] | None = None,
    approval_status: str | None = None,
    real_enqueue_result: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    preflight_result = preflight_result or {}
    dry_run_result = dry_run_result or {}
    real_enqueue_result = real_enqueue_result or {}
    return {
        "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
        "parent_task_id": task.name,
        "workflow_dir": str(workflow),
        "workflow_status": workflow_status,
        "patch_type": manifest.get("patch_type"),
        "candidate_inp_path": manifest.get("candidate_inp_path"),
        "candidate_inp_sha256": manifest.get("candidate_inp_sha256"),
        "source_inp_path": manifest.get("source_inp_path"),
        "source_inp_sha256": manifest.get("source_inp_sha256"),
        "changed_lines_count": manifest.get("changed_lines_count"),
        "unrelated_changes_count": manifest.get("unrelated_changes_count"),
        "static_validator_status": manifest.get("static_validator_status"),
        "diff_guard_status": manifest.get("diff_guard_status"),
        "physics_guard_status": manifest.get("physics_guard_status"),
        "preflight_status": preflight_result.get("status", "NOT_RUN"),
        "dry_run_enqueue_status": dry_run_result.get("status", "NOT_RUN"),
        "approval_status": approval_status or "NOT_RUN",
        "real_enqueue_status": real_enqueue_result.get("status", "NOT_RUN"),
        "queue_only": real_enqueue_result.get("queue_only"),
        "queue_file_mutated": real_enqueue_result.get("queue_file_mutated", real_enqueue_result.get("queue_mutated")),
        "solver_started": real_enqueue_result.get("solver_started"),
        "runner_started": real_enqueue_result.get("runner_started"),
        "gui_required": real_enqueue_result.get("gui_required"),
        "forbidden_mutations_detected": real_enqueue_result.get("forbidden_mutation_detected"),
        "job_id": real_enqueue_result.get("job_id") or preflight_result.get("job_id") or (request or {}).get("job_name"),
        "normalized_status": None,
        "final_pipeline_status": "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER"
        if real_enqueue_result.get("status") == "REAL_ENQUEUE_COMPLETED"
        else None,
        "solver_submitted": False,
        "queue_runner_launched": False,
        "opened_odb": False,
        "llm_executed_action": False,
        "errors": errors or list(preflight_result.get("errors", [])) + list(dry_run_result.get("errors", [])) + list(real_enqueue_result.get("errors", [])),
        "warnings": list(preflight_result.get("warnings", [])) + list(dry_run_result.get("warnings", [])) + list(real_enqueue_result.get("warnings", [])),
    }


def _status_or_block(result: dict[str, Any], success_status: str) -> str:
    return success_status if result.get("status") == "PREVIEW_READY" else "PATCH_QUEUE_PREFLIGHT_BLOCKED"


def _workflow_result(summary: dict[str, Any], workflow: Path, success: bool) -> dict[str, Any]:
    return {
        "command": "queue-patch-preview",
        "verdict": summary.get("workflow_status"),
        "success": bool(success),
        "output_paths": {
            "artifact_dir": str(workflow),
            "patch_queue_summary": str(workflow / "patch_queue_summary.json"),
            "patch_queue_summary_md": str(workflow / "patch_queue_summary.md"),
        },
        "details": summary,
        "warnings": summary.get("warnings", []),
        "errors": summary.get("errors", []),
    }


def _blocked_result(status: str, workflow_dir: str | Path | None, errors: list[str]) -> dict[str, Any]:
    workflow = Path(workflow_dir) if workflow_dir is not None else None
    return {
        "command": "queue-patch-preview",
        "verdict": status,
        "success": False,
        "output_paths": {"artifact_dir": str(workflow) if workflow else None},
        "details": {
            "workflow_status": status,
            "solver_submitted": False,
            "queue_runner_launched": False,
            "opened_odb": False,
        },
        "warnings": [],
        "errors": errors,
    }


def _approval_result(status: str, workflow: Path, success: bool, errors: list[str]) -> dict[str, Any]:
    return {
        "status": status,
        "success": success,
        "approval_token_path": str(workflow / "approvals" / "patch_queue_approval_token.json") if success else None,
        "errors": errors,
        "warnings": [],
    }


def _validation_result(status: str, valid: bool, errors: list[str], token_path: Path) -> dict[str, Any]:
    return {"status": status, "valid": valid, "approval_token_path": str(token_path), "errors": errors, "warnings": []}


def _real_enqueue_approval_report(
    approval_request: dict[str, Any],
    validation: dict[str, Any],
    preflight_result: dict[str, Any],
    dry_run_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "allow_abqjobpilot_real_enqueue": True,
        "preflight_status": approval_request["required_conditions"].get("preflight_status"),
        "dry_run_enqueue_status": approval_request["required_conditions"].get("dry_run_enqueue_status"),
        "runtime_mutation_detected": approval_request["required_conditions"].get("runtime_mutation_detected"),
        "approval_token_status": validation.get("status"),
        "allow_solver_submit": approval_request["required_conditions"].get("allow_solver_submit"),
        "submission_mode": approval_request["required_conditions"].get("submission_mode"),
        "candidate_inp_sha256_matches": True,
        "job_request_sha256_matches": True,
        "preflight_result_sha256_matches": True,
        "dry_run_result_sha256_matches": True,
        "queue_only_confirmed": dry_run_result.get("queue_only") is True or dry_run_result.get("enqueue_mode") == "queue_only",
        "dry_run_result": dry_run_result,
        "preflight_result": preflight_result,
    }


def _poll_summary(
    workflow: Path,
    manifest: dict[str, Any],
    status_result: dict[str, Any],
    output_result: dict[str, Any],
    normalized: str,
) -> dict[str, Any]:
    return {
        "schema_version": PATCH_QUEUE_SCHEMA_VERSION,
        "workflow_dir": str(workflow),
        "parent_task_id": manifest.get("parent_task_id"),
        "job_id": status_result.get("job_id") or output_result.get("job_id"),
        "raw_status": status_result.get("status"),
        "normalized_status": normalized,
        "expected_odb_path": output_result.get("expected_odb_path") or status_result.get("expected_odb_path"),
        "odb_exists": bool(output_result.get("odb_exists")),
        "lock_exists": bool(output_result.get("lock_exists") or status_result.get("lock_exists")),
        "solver_submitted": False,
        "queue_runner_launched": False,
        "opened_odb": False,
        "errors": list(status_result.get("errors", [])) + list(output_result.get("errors", [])),
        "warnings": list(status_result.get("warnings", [])) + list(output_result.get("warnings", [])),
    }


def _write_poll_artifacts(
    workflow: Path,
    request: dict[str, Any],
    status_result: dict[str, Any],
    summary: dict[str, Any],
    output_result: dict[str, Any] | None = None,
) -> None:
    output_result = output_result or {}
    write_json_artifact(workflow / "patch_queue_status_request.json", request)
    write_json_artifact(workflow / "patch_queue_status_result.json", status_result)
    write_json_artifact(workflow / "patch_queue_output_locator_result.json", output_result)
    write_json_artifact(workflow / "patch_queue_status_summary.json", summary)
    write_text_artifact(
        workflow / "patch_queue_status_summary.md",
        "# Patch Queue Status\n\n"
        f"Status: {summary.get('normalized_status')}\n\n"
        f"Job ID: {summary.get('job_id')}\n\n"
        "This poll is read-only. No solver was submitted and no ODB was opened.\n",
    )


def _poll_result(summary: dict[str, Any], workflow: Path, success: bool) -> dict[str, Any]:
    return {
        "command": "poll-patch-queue",
        "verdict": summary.get("normalized_status"),
        "success": success,
        "output_paths": {
            "artifact_dir": str(workflow),
            "patch_queue_status_summary": str(workflow / "patch_queue_status_summary.json"),
        },
        "details": summary,
        "warnings": summary.get("warnings", []),
        "errors": summary.get("errors", []),
    }


def _read_existing_task_dir(workflow: Path) -> Path:
    request = _read_json(workflow / "patch_queue_workflow_request.json")
    return Path(str(request.get("task_dir") or workflow.parent.parent))


def _read_manifest_preview_dir(workflow: Path) -> Path | None:
    manifest = _read_json(workflow / "patch_candidate_manifest.json")
    return Path(str(manifest.get("patch_preview_dir"))) if manifest.get("patch_preview_dir") else None


def _load_config(task: Path, config_path: str | Path | None) -> dict[str, Any]:
    for candidate in (config_path, task / "task_config.json", Path(__file__).resolve().parents[2] / "configs" / "sanity_demo_task.json"):
        if candidate is None:
            continue
        path = Path(candidate)
        if path.exists():
            return load_task_config(path)
    return load_task_config(None)


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")
