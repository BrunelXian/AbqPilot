from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.patching.patch_queue_workflow import poll_patch_queue


PATCHED_JOB_SCHEMA_VERSION = "0.1"
WAITING_STATUSES = {"JOB_QUEUED", "JOB_RUNNING"}


def poll_patched_job_status(
    workflow_dir: str | Path,
    abqjobpilot_root: str | Path | None = None,
) -> dict[str, Any]:
    result = poll_patch_queue(workflow_dir=workflow_dir, abqjobpilot_root=abqjobpilot_root)
    summary = dict(result.get("details", {}))
    normalized = summary.get("normalized_status")
    final_status = final_status_for_patched_job(normalized)
    summary["final_status"] = final_status
    summary["read_only"] = True
    _write_json(Path(workflow_dir) / "patch_queue_status_summary.json", summary)
    _write_text(Path(workflow_dir) / "patch_queue_status_summary.md", _render_status_markdown(summary))
    result["verdict"] = normalized
    result["details"] = summary
    result["success"] = normalized not in {"ABQJOBPILOT_UNAVAILABLE", "JOB_UNKNOWN"}
    return result


def intake_patched_job_output(
    workflow_dir: str | Path,
    manual_odb_path: str | Path | None = None,
    force_status_completed: bool = False,
) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    request = {
        "schema_version": PATCHED_JOB_SCHEMA_VERSION,
        "workflow_dir": str(workflow),
        "manual_odb_path": str(manual_odb_path) if manual_odb_path is not None else None,
        "force_status_completed": bool(force_status_completed),
        "opened_odb": False,
        "submitted_solver": False,
        "queue_runner_launched": False,
    }
    manifest = _read_json(workflow / "patch_candidate_manifest.json")
    status_summary = _read_json(workflow / "patch_queue_status_summary.json")
    normalized = status_summary.get("normalized_status")
    expected_odb = status_summary.get("expected_odb_path")
    manual_validation = validate_manual_odb(manual_odb_path) if manual_odb_path is not None else None

    verdict = "WAITING_FOR_PATCHED_JOB"
    accepted_odb_path = None
    odb_exists = bool(status_summary.get("odb_exists"))
    lock_exists = bool(status_summary.get("lock_exists"))
    output_accepted = False
    errors: list[str] = []
    warnings: list[str] = []

    if manual_validation is not None:
        verdict = manual_validation["verdict"]
        errors.extend(manual_validation.get("errors", []))
        if manual_validation["accepted"]:
            accepted_odb_path = manual_validation["path"]
            odb_exists = True
            lock_exists = False
            output_accepted = True
            normalized = "JOB_OUTPUTS_READY"
            verdict = "PATCHED_JOB_OUTPUT_ACCEPTED"
    elif normalized == "JOB_OUTPUTS_READY" or force_status_completed:
        candidate_path = Path(str(expected_odb or ""))
        if expected_odb and candidate_path.exists() and candidate_path.suffix.lower() == ".odb":
            lock_path = candidate_path.with_suffix(".lck")
            if lock_path.exists():
                verdict = "PATCHED_JOB_OUTPUT_REJECTED_LOCKED"
                lock_exists = True
                errors.append(f"lock file exists beside ODB: {lock_path}")
            else:
                accepted_odb_path = str(candidate_path)
                odb_exists = True
                lock_exists = False
                output_accepted = True
                verdict = "PATCHED_JOB_OUTPUT_ACCEPTED"
        else:
            verdict = "WAITING_FOR_PATCHED_JOB_OUTPUTS"
            warnings.append("patched job output ODB is not available yet")
    elif normalized in WAITING_STATUSES or not normalized:
        verdict = "WAITING_FOR_PATCHED_JOB"
        warnings.append("patched job is still queued or running")
    elif normalized == "JOB_ODB_MISSING":
        verdict = "WAITING_FOR_PATCHED_JOB_OUTPUTS"
        warnings.append("patched job reports completion, but the expected ODB is missing")
    elif normalized == "JOB_FAILED":
        verdict = "PATCHED_JOB_FAILED"
        errors.append("patched job status indicates failure")
    elif normalized == "JOB_LOCKED":
        verdict = "PATCHED_JOB_OUTPUT_REJECTED_LOCKED"
        lock_exists = True
        errors.append("patched job output appears locked")
    else:
        verdict = str(normalized or "JOB_UNKNOWN")

    summary = {
        "schema_version": PATCHED_JOB_SCHEMA_VERSION,
        "workflow_dir": str(workflow),
        "job_id": status_summary.get("job_id"),
        "candidate_inp_path": manifest.get("candidate_inp_path"),
        "candidate_inp_sha256": manifest.get("candidate_inp_sha256"),
        "latest_normalized_status": normalized,
        "manual_odb_path": request["manual_odb_path"],
        "expected_odb_path": expected_odb,
        "accepted_odb_path": accepted_odb_path,
        "odb_exists": odb_exists,
        "lock_exists": lock_exists,
        "output_accepted": output_accepted,
        "verdict": verdict,
        "opened_odb": False,
        "submitted_solver": False,
        "queue_runner_launched": False,
        "next_allowed_action": _next_action(verdict),
        "errors": errors,
        "warnings": warnings,
    }
    _write_json(workflow / "patched_job_output_intake_request.json", request)
    _write_json(workflow / "patched_job_output_intake_result.json", summary)
    _write_json(workflow / "patched_job_output_intake_summary.json", summary)
    _write_text(workflow / "patched_job_output_intake_summary.md", _render_intake_markdown(summary))
    return {
        "command": "intake-patched-job-output",
        "verdict": verdict,
        "success": not errors or verdict in {"WAITING_FOR_PATCHED_JOB", "WAITING_FOR_PATCHED_JOB_OUTPUTS"},
        "output_paths": {
            "artifact_dir": str(workflow),
            "patched_job_output_intake_summary": str(workflow / "patched_job_output_intake_summary.json"),
            "patched_job_output_intake_result": str(workflow / "patched_job_output_intake_result.json"),
        },
        "details": summary,
        "errors": errors,
        "warnings": warnings,
    }


def validate_manual_odb(path: str | Path | None) -> dict[str, Any]:
    target = Path(path) if path is not None else None
    if target is None:
        return {"accepted": False, "verdict": "PATCHED_JOB_OUTPUT_REJECTED_INVALID_PATH", "errors": ["manual ODB path is required"]}
    if not target.exists():
        return {
            "accepted": False,
            "verdict": "PATCHED_JOB_OUTPUT_REJECTED_MISSING",
            "path": str(target),
            "errors": [f"ODB does not exist: {target}"],
        }
    if target.suffix.lower() != ".odb":
        return {
            "accepted": False,
            "verdict": "PATCHED_JOB_OUTPUT_REJECTED_INVALID_PATH",
            "path": str(target),
            "errors": [f"manual output is not an .odb file: {target}"],
        }
    lock_path = target.with_suffix(".lck")
    if lock_path.exists():
        return {
            "accepted": False,
            "verdict": "PATCHED_JOB_OUTPUT_REJECTED_LOCKED",
            "path": str(target),
            "errors": [f"lock file exists beside ODB: {lock_path}"],
        }
    return {"accepted": True, "verdict": "PATCHED_JOB_OUTPUT_ACCEPTED", "path": str(target), "errors": []}


def final_status_for_patched_job(normalized_status: str | None) -> str:
    if normalized_status in WAITING_STATUSES:
        return "WAITING_FOR_PATCHED_JOB"
    if normalized_status == "JOB_FAILED":
        return "PATCHED_JOB_FAILED"
    if normalized_status == "JOB_ODB_MISSING":
        return "WAITING_FOR_PATCHED_JOB_OUTPUTS"
    if normalized_status == "JOB_OUTPUTS_READY":
        return "JOB_OUTPUTS_READY"
    if normalized_status == "JOB_LOCKED":
        return "PATCHED_JOB_OUTPUT_REJECTED_LOCKED"
    if normalized_status == "ABQJOBPILOT_UNAVAILABLE":
        return "ABQJOBPILOT_UNAVAILABLE"
    return "JOB_UNKNOWN"


def _next_action(verdict: str) -> str:
    if verdict == "PATCHED_JOB_OUTPUT_ACCEPTED":
        return "Run extract-patched-job-metrics through the existing gated ODB metrics path."
    if verdict == "WAITING_FOR_PATCHED_JOB":
        return "Poll patch queue status again or run external solver outside AbqPilot."
    if verdict == "WAITING_FOR_PATCHED_JOB_OUTPUTS":
        return "Wait for an existing patched ODB or provide --manual-odb-path."
    if verdict == "PATCHED_JOB_FAILED":
        return "Review abqjobpilot status artifacts and solver logs outside AbqPilot."
    return "No automatic action is allowed."


def _render_status_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Patch Queue Status",
            "",
            f"Status: `{summary.get('normalized_status')}`",
            f"Final status: `{summary.get('final_status')}`",
            f"Job ID: `{summary.get('job_id')}`",
            "",
            "This poll is read-only. No solver was submitted, no queue runner was launched, and no ODB was opened.",
        ]
    ) + "\n"


def _render_intake_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Patched Job Output Intake",
            "",
            f"Verdict: `{summary.get('verdict')}`",
            f"Job ID: `{summary.get('job_id')}`",
            f"Latest status: `{summary.get('latest_normalized_status')}`",
            f"Expected ODB: `{summary.get('expected_odb_path')}`",
            f"Manual ODB: `{summary.get('manual_odb_path')}`",
            f"Accepted ODB: `{summary.get('accepted_odb_path')}`",
            f"Output accepted: `{summary.get('output_accepted')}`",
            "",
            "## Safety",
            "",
            "- Opened ODB: `False`",
            "- Submitted solver: `False`",
            "- Launched " + "Queue" + "Runner: `False`",
        ]
    ) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
