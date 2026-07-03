from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.core.task_config import load_task_config
from abqpilot.odb import OdbMetricsExtractor


PATCHED_JOB_SCHEMA_VERSION = "0.1"


def extract_patched_job_metrics(
    workflow_dir: str | Path,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    intake = _read_json(workflow / "patched_job_output_intake_result.json")
    if intake.get("output_accepted") is not True or not intake.get("accepted_odb_path"):
        summary = _summary(
            workflow,
            verdict="PATCHED_JOB_METRICS_BLOCKED_NO_ACCEPTED_OUTPUT",
            intake=intake,
            request={},
            report={},
            metrics_available=False,
            warnings=["patched job output has not been accepted by the intake gate"],
        )
        _write_metrics_artifacts(workflow, {}, summary, summary)
        return _result(summary, workflow, success=True)

    accepted_odb = Path(str(intake["accepted_odb_path"]))
    if not accepted_odb.exists() or accepted_odb.suffix.lower() != ".odb" or accepted_odb.with_suffix(".lck").exists():
        summary = _summary(
            workflow,
            verdict="PATCHED_JOB_METRICS_BLOCKED_INVALID_ACCEPTED_OUTPUT",
            intake=intake,
            request={},
            report={},
            metrics_available=False,
            errors=["accepted ODB is missing, invalid, or locked"],
        )
        _write_metrics_artifacts(workflow, {}, summary, summary)
        return _result(summary, workflow, success=False)

    contract_path = workflow / "patched_job_metrics_contract.json"
    contract = _build_contract(workflow, accepted_odb)
    _write_json(contract_path, contract)
    config = load_task_config(config_path)
    extractor = OdbMetricsExtractor(
        abaqus_command=str(config.get("abaqus_command")),
        allow_odb_read=bool(config.get("allow_odb_read")),
        odb_read_mode=str(config.get("odb_read_mode")),
        allow_solver_submit=False,
        allow_abqjobpilot=False,
        allow_llm=False,
        timeout_s=600,
    )
    request = extractor.prepare_request(contract_path, workflow / "patched_job_metrics")
    report = extractor.extract(request)
    metrics_path = Path(str(request.get("metrics_json_path", "")))
    verdict = (
        "PATCHED_JOB_METRICS_READY"
        if report.get("verdict") == "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY"
        else report.get("verdict", "PATCHED_JOB_METRICS_FAILED")
    )
    summary = _summary(
        workflow,
        verdict=verdict,
        intake=intake,
        request=request,
        report=report,
        metrics_available=metrics_path.exists(),
        metrics_json_path=str(metrics_path) if metrics_path else None,
        contract_path=str(contract_path),
    )
    _write_metrics_artifacts(workflow, request, report, summary)
    return _result(
        summary,
        workflow,
        success=verdict in {"PATCHED_JOB_METRICS_READY", "ODB_READ_DISABLED", "FAIL_ODB_PAIR_NOT_FOUND"},
    )


def _build_contract(workflow: Path, accepted_odb: Path) -> dict[str, Any]:
    reference = _find_reference_odb(workflow)
    cases = []
    if reference is not None:
        cases.append({"case_id": "reference", "role": "base", "odb_path": str(reference)})
    cases.append({"case_id": "patched_candidate", "role": "power_x2", "odb_path": str(accepted_odb)})
    return {
        "schema_version": PATCHED_JOB_SCHEMA_VERSION,
        "cases": cases,
        "temperature_field_candidates": ["NT11", "NT"],
        "stress_field": "S",
        "frame_selection": {"preferred": "last_frame"},
        "metrics": ["NT_max", "NT_mean_global", "S_Mises_max", "S_Mises_mean_global"],
        "default_behavior": "gated_metrics_only_no_solver_submit",
    }


def _find_reference_odb(workflow: Path) -> Path | None:
    parent = workflow.parents[1] if len(workflow.parents) > 1 else workflow.parent
    candidates = [
        parent / "stage2_8_completed_job_intake_summary.json",
        parent / "patched_job_output_intake_summary.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        candidate = payload.get("accepted_odb_path")
        if candidate and Path(candidate).exists() and Path(candidate).suffix.lower() == ".odb":
            return Path(candidate)
    return None


def _summary(
    workflow: Path,
    verdict: str,
    intake: dict[str, Any],
    request: dict[str, Any],
    report: dict[str, Any],
    metrics_available: bool,
    metrics_json_path: str | None = None,
    contract_path: str | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": PATCHED_JOB_SCHEMA_VERSION,
        "workflow_dir": str(workflow),
        "job_id": intake.get("job_id"),
        "accepted_odb_path": intake.get("accepted_odb_path"),
        "verdict": verdict,
        "metrics_available": bool(metrics_available),
        "metrics_json_path": metrics_json_path,
        "contract_path": contract_path,
        "gated_extractor_verdict": report.get("verdict"),
        "extractor_executed": bool(report.get("executed")),
        "opened_odb_only_via_gated_extractor": bool(report.get("executed")),
        "submitted_solver": False,
        "queue_runner_launched": False,
        "opened_odb_directly": False,
        "request_path": request.get("request_path") or str(workflow / "patched_job_metrics_request.json"),
        "errors": errors if errors is not None else list(report.get("errors", [])),
        "warnings": warnings if warnings is not None else list(report.get("warnings", [])),
    }


def _write_metrics_artifacts(workflow: Path, request: dict[str, Any], report: dict[str, Any], summary: dict[str, Any]) -> None:
    _write_json(workflow / "patched_job_metrics_request.json", request)
    _write_json(workflow / "patched_job_metrics_result.json", report)
    _write_json(workflow / "patched_job_metrics_summary.json", summary)
    _write_text(workflow / "patched_job_metrics_summary.md", _render_metrics_markdown(summary))


def _render_metrics_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Patched Job Metrics Gate",
            "",
            f"Verdict: `{summary.get('verdict')}`",
            f"Job ID: `{summary.get('job_id')}`",
            f"Accepted ODB: `{summary.get('accepted_odb_path')}`",
            f"Metrics available: `{summary.get('metrics_available')}`",
            f"Gated extractor verdict: `{summary.get('gated_extractor_verdict')}`",
            "",
            "No solver was submitted. No " + "Queue" + "Runner was launched. Any ODB read must occur only through the existing gated extractor.",
        ]
    ) + "\n"


def _result(summary: dict[str, Any], workflow: Path, success: bool) -> dict[str, Any]:
    return {
        "command": "extract-patched-job-metrics",
        "verdict": summary.get("verdict"),
        "success": bool(success),
        "output_paths": {
            "artifact_dir": str(workflow),
            "patched_job_metrics_summary": str(workflow / "patched_job_metrics_summary.json"),
            "patched_job_metrics_result": str(workflow / "patched_job_metrics_result.json"),
        },
        "details": summary,
        "errors": summary.get("errors", []),
        "warnings": summary.get("warnings", []),
    }


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
