from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.odb import OdbMetricsExtractor
from abqpilot.solver.solver_artifacts import read_json, result, write_json, write_text
from abqpilot.solver.solver_monitor import classify_solver_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_ODB = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_power_1x.odb"
RUNTIME_CONFIG = PROJECT_ROOT / "abqpilot" / "configs" / "abaqus_runtime.yaml"


def intake_solver_run_output(solver_run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    monitor = classify_solver_run(run_dir)
    odb = Path(monitor["odb_path"])
    accepted = (
        monitor["status"] == "SOLVER_COMPLETED"
        and monitor.get("diagnosis_status") == "JOB_COMPLETED_ODB_ACCEPTABLE"
        and monitor.get("odb_acceptable_for_metrics") is True
        and odb.exists()
        and not monitor["lock_exists"]
    )
    verdict = "SOLVER_OUTPUT_ACCEPTED" if accepted else "SOLVER_OUTPUT_NOT_READY"
    details = {
        "stage": "Stage 4.0",
        "solver_run_dir": str(run_dir),
        "monitor_status": monitor["status"],
        "accepted_odb_path": str(odb) if accepted else None,
        "expected_odb_exists": odb.exists(),
        "lock_exists": monitor["lock_exists"],
        "diagnosis_status": monitor.get("diagnosis_status"),
        "failure_category": monitor.get("failure_category"),
        "odb_acceptable_for_metrics": monitor.get("odb_acceptable_for_metrics"),
        "solver_output_accepted": accepted,
        "opened_odb": False,
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
        "errors": [] if accepted else ["solver output is not diagnosed as completed and acceptable for metrics"],
        "warnings": [],
    }
    write_json(run_dir / "solver_output_intake_result.json", details)
    return result("intake-solver-run-output", verdict, accepted, run_dir, details)


def report_solver_run(
    solver_run_dir: str | Path,
    runtime_config: str | Path = RUNTIME_CONFIG,
    baseline_odb: str | Path = BASELINE_ODB,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    intake = read_json(run_dir / "solver_output_intake_result.json")
    accepted_odb = Path(str(intake.get("accepted_odb_path", "")))
    if intake.get("solver_output_accepted") is not True or not accepted_odb.exists():
        details = {
            "stage": "Stage 4.0",
            "solver_run_dir": str(run_dir),
            "verdict": "SOLVER_REPORT_BLOCKED_NO_ACCEPTED_OUTPUT",
            "solver_metrics_available": False,
            "solver_report_written": False,
            "submitted_solver": False,
            "queue_runner_launched": False,
            "opened_odb_directly": False,
            "errors": ["solver output has not been accepted"],
            "warnings": [],
        }
        write_json(run_dir / "solver_metrics_result.json", details)
        write_json(run_dir / "solver_report.json", details)
        write_text(run_dir / "solver_report.md", _render_report_md(details))
        _write_stage4_summary(run_dir, details)
        return result("report-solver-run", "SOLVER_REPORT_BLOCKED_NO_ACCEPTED_OUTPUT", False, run_dir, details)

    contract_path = run_dir / "solver_metrics_contract.json"
    contract = _build_contract(Path(baseline_odb), accepted_odb)
    write_json(contract_path, contract)
    runtime = _load_runtime_config(Path(runtime_config))
    extractor = OdbMetricsExtractor(
        abaqus_command=str(runtime.get("abaqus_command")),
        allow_odb_read=bool(runtime.get("allow_odb_read")),
        odb_read_mode=str(runtime.get("odb_read_mode", "metrics_only")),
        allow_solver_submit=False,
        allow_abqjobpilot=False,
        allow_llm=False,
        timeout_s=600,
    )
    metrics_dir = run_dir / "solver_gated_odb_metrics"
    request = extractor.prepare_request(contract_path, metrics_dir)
    report = extractor.extract(request)
    metrics_path = Path(str(request.get("metrics_json_path", "")))
    metrics_payload = read_json(metrics_path) if metrics_path.exists() else {}
    base = _case_by_role(metrics_payload, "base").get("metrics", {})
    candidate = _case_by_role(metrics_payload, "power_x2").get("metrics", {})
    comparison = _comparison(base, candidate)
    verdict = _evaluation_verdict(comparison, bool(base), bool(candidate))
    metrics_result = {
        "stage": "Stage 4.0",
        "solver_run_dir": str(run_dir),
        "verdict": "SOLVER_METRICS_READY"
        if report.get("verdict") == "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY"
        else report.get("verdict", "SOLVER_METRICS_FAILED"),
        "solver_metrics_available": bool(metrics_payload),
        "metrics_json_path": str(metrics_path),
        "gated_extractor_verdict": report.get("verdict"),
        "opened_odb_only_via_gated_extractor": bool(report.get("executed")),
        "submitted_solver": False,
        "queue_runner_launched": False,
        "opened_odb_directly": False,
        "errors": list(report.get("errors", [])),
        "warnings": [],
    }
    solver_report = {
        "stage": "Stage 4.0",
        "solver_run_dir": str(run_dir),
        "evaluation_verdict": verdict,
        "accepted_odb_path": str(accepted_odb),
        "baseline_odb_path": str(baseline_odb),
        "solver_metrics_available": bool(candidate),
        "reference_metrics_available": bool(base),
        "comparison_available": bool(comparison),
        "field_temperature": _case_by_role(metrics_payload, "power_x2").get("temperature_field_used"),
        "base_metrics": base,
        "solver_metrics": candidate,
        "comparison": comparison,
        "opened_odb_only_via_gated_extractor": bool(report.get("executed")),
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
        "opened_odb_directly": False,
        "errors": metrics_result["errors"],
        "warnings": [],
    }
    write_json(run_dir / "solver_metrics_result.json", metrics_result)
    write_json(run_dir / "solver_report.json", solver_report)
    write_text(run_dir / "solver_report.md", _render_report_md(solver_report))
    _write_stage4_summary(run_dir, solver_report)
    return result("report-solver-run", verdict, bool(candidate), run_dir, solver_report)


def _write_stage4_summary(run_dir: Path, report_payload: dict[str, Any]) -> None:
    run_result = read_json(run_dir / "solver_run_result.json")
    monitor = read_json(run_dir / "solver_monitor_result.json") or classify_solver_run(run_dir)
    intake = read_json(run_dir / "solver_output_intake_result.json")
    summary = {
        "stage": "Stage 4.0",
        "verdict": (
            "PASS_ABQPILOT_V2_STAGE4_0_CONTROLLED_SOLVER_AUTOMATION_READY"
            if report_payload.get("solver_metrics_available")
            else report_payload.get("verdict", "CONTROLLED_SOLVER_RUN_FAILED")
        ),
        "solver_run_dir": str(run_dir),
        "expected_odb_path": monitor.get("odb_path"),
        "monitor_status": monitor.get("status"),
        "expected_odb_exists": monitor.get("odb_exists"),
        "lock_exists_after_completion": monitor.get("lock_exists"),
        "solver_output_accepted": intake.get("solver_output_accepted"),
        "solver_metrics_available": report_payload.get("solver_metrics_available", False),
        "solver_report_written": True,
        "report_verdict": report_payload.get("evaluation_verdict") or report_payload.get("verdict"),
        "solver_launched": run_result.get("solver_launched", False),
        "queue_runner_launched": False,
        "abqjobpilot_gui_launched": False,
        "llm_execution_authority": False,
        "created_new_queue_job": False,
        "opened_odb_directly": False,
    }
    write_json(run_dir / "stage4_0_controlled_solver_automation_summary.json", summary)
    write_text(run_dir / "stage4_0_controlled_solver_automation_summary.md", _render_summary_md(summary))


def _build_contract(baseline_odb: Path, accepted_odb: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "cases": [
            {"case_id": "base_power_1x", "role": "base", "odb_path": str(baseline_odb)},
            {"case_id": "controlled_solver_candidate", "role": "power_x2", "odb_path": str(accepted_odb)},
        ],
        "temperature_field_candidates": ["NT11", "NT"],
        "stress_field": "S",
        "frame_selection": {"preferred": "last_frame", "cooling_time_s": 100.0},
        "metrics": ["NT_max", "NT_mean_global", "S_Mises_max", "S_Mises_mean_global"],
        "default_behavior": "gated_metrics_only_no_solver_submit",
    }


def _evaluation_verdict(comparison: dict[str, Any], reference_available: bool, solver_available: bool) -> str:
    if not reference_available or not solver_available:
        return "CONTROLLED_SOLVER_INSUFFICIENT_REFERENCE"
    nt_delta = comparison.get("NT_max_delta")
    stress_delta = comparison.get("S_Mises_max_delta")
    if nt_delta is not None and stress_delta is not None and nt_delta > 0 and stress_delta < 0:
        return "CONTROLLED_SOLVER_MIXED_RESPONSE"
    return "CONTROLLED_SOLVER_METRICS_READY"


def _comparison(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key in ["NT_max", "NT_mean_global", "S_Mises_max", "S_Mises_mean_global"]:
        left = base.get(key)
        right = candidate.get(key)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            data[f"{key}_delta"] = right - left
            data[f"{key}_ratio"] = None if left == 0 else right / left
    return data


def _case_by_role(metrics: dict[str, Any], role: str) -> dict[str, Any]:
    for case in metrics.get("cases", []):
        if case.get("role") == role:
            return case
    return {}


def _render_report_md(report_payload: dict[str, Any]) -> str:
    solver = report_payload.get("solver_metrics", {})
    base = report_payload.get("base_metrics", {})
    return "\n".join(
        [
            "# Stage 4.0 Controlled Solver Report",
            "",
            f"Verdict: `{report_payload.get('evaluation_verdict') or report_payload.get('verdict')}`",
            f"Accepted ODB: `{report_payload.get('accepted_odb_path')}`",
            f"Base NT_max: `{base.get('NT_max')}`",
            f"Solver NT_max: `{solver.get('NT_max')}`",
            f"Base S_Mises_max: `{base.get('S_Mises_max')}`",
            f"Solver S_Mises_max: `{solver.get('S_Mises_max')}`",
            "",
            "No external queue worker was launched. No LLM executed solver actions. ODB metrics used the gated extractor.",
        ]
    ) + "\n"


def _render_summary_md(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Stage 4.0 Controlled Solver Automation Summary",
            "",
            f"Verdict: `{summary.get('verdict')}`",
            f"Monitor status: `{summary.get('monitor_status')}`",
            f"Expected ODB exists: `{summary.get('expected_odb_exists')}`",
            f"Solver output accepted: `{summary.get('solver_output_accepted')}`",
            f"Solver metrics available: `{summary.get('solver_metrics_available')}`",
            f"Report verdict: `{summary.get('report_verdict')}`",
        ]
    ) + "\n"


def _load_runtime_config(path: Path) -> dict[str, Any]:
    runtime: dict[str, Any] = {}
    in_runtime = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("runtime:"):
            in_runtime = True
            continue
        if not in_runtime or not raw_line.startswith("  "):
            continue
        key, value = raw_line.strip().split(":", 1)
        runtime[key] = _parse_scalar(value.strip())
    return runtime


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value
