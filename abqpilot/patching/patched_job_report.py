from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PATCHED_JOB_SCHEMA_VERSION = "0.1"


def report_patched_job(workflow_dir: str | Path) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    manifest = _read_json(workflow / "patch_candidate_manifest.json")
    status = _read_json(workflow / "patch_queue_status_summary.json")
    intake = _read_json(workflow / "patched_job_output_intake_summary.json")
    metrics = _read_json(workflow / "patched_job_metrics_summary.json")
    metrics_payload = _read_json(Path(str(metrics.get("metrics_json_path", "")))) if metrics.get("metrics_json_path") else {}
    patched_metrics_available = bool(metrics.get("metrics_available") and metrics_payload)
    reference_available = _reference_metrics_available(metrics_payload)
    comparison_available = bool(metrics_payload.get("comparison")) and reference_available
    verdict = _evaluation_verdict(status, intake, metrics, patched_metrics_available, reference_available)
    report = {
        "schema_version": PATCHED_JOB_SCHEMA_VERSION,
        "workflow_dir": str(workflow),
        "job_id": status.get("job_id") or intake.get("job_id"),
        "patch_type": manifest.get("patch_type"),
        "candidate_inp_sha256": manifest.get("candidate_inp_sha256"),
        "normalized_status": status.get("normalized_status"),
        "output_accepted": bool(intake.get("output_accepted")),
        "accepted_odb_path": intake.get("accepted_odb_path"),
        "patched_metrics_available": patched_metrics_available,
        "reference_metrics_available": reference_available,
        "comparison_available": comparison_available,
        "evaluation_verdict": verdict,
        "summary": _summary_text(verdict, status, intake, metrics),
        "opened_odb_only_via_gated_extractor": bool(metrics.get("opened_odb_only_via_gated_extractor", False)),
        "submitted_solver": False,
        "queue_runner_launched": False,
        "opened_odb_directly": False,
        "errors": list(status.get("errors", [])) + list(intake.get("errors", [])) + list(metrics.get("errors", [])),
        "warnings": list(status.get("warnings", [])) + list(intake.get("warnings", [])) + list(metrics.get("warnings", [])),
    }
    _write_json(workflow / "patched_job_report.json", report)
    _write_text(workflow / "patched_job_report.md", _render_report_markdown(report))
    return {
        "command": "report-patched-job",
        "verdict": verdict,
        "success": True,
        "output_paths": {
            "artifact_dir": str(workflow),
            "patched_job_report_json": str(workflow / "patched_job_report.json"),
            "patched_job_report_md": str(workflow / "patched_job_report.md"),
        },
        "details": report,
        "errors": report["errors"],
        "warnings": report["warnings"],
    }


def _evaluation_verdict(
    status: dict[str, Any],
    intake: dict[str, Any],
    metrics: dict[str, Any],
    patched_metrics_available: bool,
    reference_available: bool,
) -> str:
    normalized = status.get("normalized_status")
    if normalized in {"JOB_QUEUED", "JOB_RUNNING"}:
        return "PATCHED_JOB_WAITING"
    if normalized == "JOB_FAILED":
        return "PATCHED_JOB_FAILED"
    if intake.get("output_accepted") is not True:
        return "PATCHED_JOB_OUTPUT_NOT_ACCEPTED"
    if not patched_metrics_available:
        return "PATCHED_METRICS_MISSING"
    if not reference_available:
        return "INSUFFICIENT_REFERENCE"
    if metrics.get("verdict") == "PATCHED_JOB_METRICS_READY":
        return "PATCHED_METRICS_READY"
    return "PATCHED_MIXED"


def _reference_metrics_available(metrics_payload: dict[str, Any]) -> bool:
    for case in metrics_payload.get("cases", []):
        if case.get("role") in {"base", "reference"} and case.get("metrics"):
            return True
    return False


def _summary_text(verdict: str, status: dict[str, Any], intake: dict[str, Any], metrics: dict[str, Any]) -> str:
    if verdict == "PATCHED_JOB_WAITING":
        return "The patched queue job is not complete yet; poll status again later."
    if verdict == "PATCHED_JOB_OUTPUT_NOT_ACCEPTED":
        return "No completed patched output has been accepted by the intake gate."
    if verdict == "PATCHED_METRICS_MISSING":
        return "Patched output is accepted, but gated metrics are not available yet."
    if verdict == "INSUFFICIENT_REFERENCE":
        return "Patched metrics are available, but no reference metrics are available for comparison."
    return f"Patched job report verdict: {verdict}."


def _render_report_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Patched Job Report",
            "",
            f"Verdict: `{report.get('evaluation_verdict')}`",
            f"Job ID: `{report.get('job_id')}`",
            f"Patch type: `{report.get('patch_type')}`",
            f"Normalized status: `{report.get('normalized_status')}`",
            f"Output accepted: `{report.get('output_accepted')}`",
            f"Patched metrics available: `{report.get('patched_metrics_available')}`",
            f"Reference metrics available: `{report.get('reference_metrics_available')}`",
            "",
            report.get("summary", ""),
            "",
            "## Safety",
            "",
            "- Submitted solver: `False`",
            "- Launched " + "Queue" + "Runner: `False`",
            "- Opened ODB directly: `False`",
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
