from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.patching.patch_application import apply_patch_proposal_preview
from abqpilot.patching.patch_artifacts import render_patch_preview_summary, write_patch_preview_artifacts
from abqpilot.patching.patch_validation import resolve_source_inp, validate_patch_preview_request
from abqpilot.tools.diff_guard_tool import DiffGuard
from abqpilot.tools.physics_guard_tool import PhysicsGuard
from abqpilot.tools.static_validator_tool import StaticValidator


def preview_patch(
    task_dir: str | Path,
    proposal_path: str | Path | None = None,
    source_inp: str | Path | None = None,
    dry_run: bool = False,
    force_no_write: bool = False,
) -> dict[str, Any]:
    task = Path(task_dir)
    task_id = task.name
    proposal_file = Path(proposal_path) if proposal_path is not None else task / "llm_patch_proposals" / "llm_candidate_patch_proposal.json"
    artifact_dir = task / "patch_previews" / ("preview_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    proposal = _read_json(proposal_file)
    if not proposal:
        summary = _summary(task_id, proposal_file, None, "PATCH_PREVIEW_BLOCKED_NO_VALID_PROPOSAL")
        paths = _write_summary_only(artifact_dir, summary)
        return _result(summary, paths)

    validation = validate_patch_preview_request(proposal)
    candidate = proposal.get("candidate_patch", {}) if isinstance(proposal.get("candidate_patch"), dict) else {}
    patch_type = candidate.get("patch_type")
    if not validation.get("allowed"):
        summary = _summary(task_id, proposal_file, proposal, validation["status"])
        summary["errors"] = validation.get("errors", [])
        summary["proposal_validation"] = validation.get("proposal_validation")
        paths = _write_summary_only(artifact_dir, summary)
        return _result(summary, paths)

    source = resolve_source_inp(task, source_inp)
    if source is None:
        summary = _summary(task_id, proposal_file, proposal, "PATCH_PREVIEW_BLOCKED_TARGET_NOT_IDENTIFIED")
        summary["errors"] = ["source INP could not be resolved"]
        paths = _write_summary_only(artifact_dir, summary)
        return _result(summary, paths)

    candidate_inp = artifact_dir / f"{source.stem}__patch_preview.inp"
    write_candidate = not dry_run and not force_no_write
    application = apply_patch_proposal_preview(proposal, source, candidate_inp, dry_run=not write_candidate)
    static_report: dict[str, Any] = {"tool": "StaticValidator", "passed": False, "skipped": True}
    diff_report: dict[str, Any] = {"tool": "DiffGuard", "allowed": False, "skipped": True, "changed_lines": []}
    physics_report: dict[str, Any] = {"tool": "PhysicsGuard", "passed": False, "skipped": True}
    preview_status = "PATCH_PREVIEW_READY"
    if not application.get("allowed"):
        preview_status = application.get("status", "PATCH_PREVIEW_BLOCKED")
    elif write_candidate:
        static_report = StaticValidator().validate(candidate_inp, target_region=None)
        diff_report = DiffGuard().compare(source, candidate_inp)
        physics_report = PhysicsGuard().check(diff_report)
        if not (static_report.get("passed") and diff_report.get("allowed") and physics_report.get("passed")):
            preview_status = "PATCH_PREVIEW_FAILED_VALIDATION"
    else:
        preview_status = "PATCH_PREVIEW_DRY_RUN_READY"

    changed_lines = diff_report.get("changed_lines", []) if isinstance(diff_report, dict) else []
    intended_lines = {change.get("line_index") for change in application.get("changed_lines", [])}
    unrelated_changes_count = len([line for line in changed_lines if line.get("line_index") not in intended_lines])
    summary = _summary(task_id, proposal_file, proposal, preview_status)
    summary.update(
        {
            "source_inp_path": str(source),
            "candidate_inp_path": str(candidate_inp) if write_candidate and candidate_inp.exists() else None,
            "changed_lines_count": len(changed_lines) if changed_lines else len(application.get("changed_lines", [])),
            "unrelated_changes_count": unrelated_changes_count,
            "static_validator_status": _status(static_report, "passed"),
            "diff_guard_status": _status(diff_report, "allowed"),
            "physics_guard_status": _status(physics_report, "passed"),
            "errors": application.get("errors", []),
        }
    )
    payloads = {
        "source_inp_path.txt": str(source),
        "candidate_inp_path.txt": str(candidate_inp) if write_candidate and candidate_inp.exists() else "",
        "patch_application_request.json": application.get("request", {}),
        "patch_application_result.json": application,
        "patch_diff_report.json": {"changed_lines": changed_lines},
        "static_validation_report.json": static_report,
        "diff_guard_report.json": diff_report,
        "physics_guard_report.json": physics_report,
        "patch_preview_summary.json": summary,
        "patch_preview_summary.md": render_patch_preview_summary(summary),
    }
    paths = write_patch_preview_artifacts(artifact_dir, payloads)
    return _result(summary, paths)


def _summary(task_id: str, proposal_path: Path, proposal: dict[str, Any] | None, status: str) -> dict[str, Any]:
    candidate = proposal.get("candidate_patch", {}) if isinstance(proposal, dict) else {}
    return {
        "schema_version": "0.1",
        "task_id": task_id,
        "proposal_path": str(proposal_path),
        "proposal_verdict": proposal.get("proposal_verdict") if isinstance(proposal, dict) else None,
        "patch_type": candidate.get("patch_type"),
        "preview_status": status,
        "source_inp_path": None,
        "candidate_inp_path": None,
        "changed_lines_count": 0,
        "unrelated_changes_count": 0,
        "static_validator_status": "SKIPPED",
        "diff_guard_status": "SKIPPED",
        "physics_guard_status": "SKIPPED",
        "solver_submitted": False,
        "job_enqueued": False,
        "queue_runner_launched": False,
        "opened_odb": False,
        "requires_human_review": True,
        "next_allowed_action": "Human review the candidate INP and optionally run existing guarded prepare/enqueue flow in a future stage.",
    }


def _write_summary_only(artifact_dir: Path, summary: dict[str, Any]) -> dict[str, str]:
    return write_patch_preview_artifacts(
        artifact_dir,
        {
            "patch_preview_summary.json": summary,
            "patch_preview_summary.md": render_patch_preview_summary(summary),
        },
    )


def _result(summary: dict[str, Any], paths: dict[str, str]) -> dict[str, Any]:
    return {
        "command": "preview-patch",
        "verdict": summary["preview_status"],
        "success": summary["preview_status"] in {"PATCH_PREVIEW_READY", "PATCH_PREVIEW_NOT_APPLICABLE", "PATCH_PREVIEW_DRY_RUN_READY"},
        "output_paths": paths | {"artifact_dir": str(Path(paths["patch_preview_summary"]).parent)},
        "details": summary,
        "warnings": [],
        "errors": summary.get("errors", []),
    }


def _status(report: dict[str, Any], field: str) -> str:
    if report.get("skipped"):
        return "SKIPPED"
    return "PASS" if report.get(field) else "FAIL"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
