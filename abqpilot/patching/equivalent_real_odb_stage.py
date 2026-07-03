from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file
from abqpilot.odb import OdbMetricsExtractor
from abqpilot.patching.real_sanity_base_candidate import CANDIDATE_HEAT_LINE, SOURCE_HEAT_LINE


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGE3_9B_DIR = PROJECT_ROOT / "runs" / "stage3_9b_real_sanity_base_patch_candidate"
STAGE3_9C_DIR = PROJECT_ROOT / "runs" / "stage3_9c_equivalent_real_odb_intake_metrics_report"
POWER_1X_ODB = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_power_1x.odb"
POWER_2X_ODB = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_power_2x.odb"
RUNTIME_CONFIG = PROJECT_ROOT / "abqpilot" / "configs" / "abaqus_runtime.yaml"


def run_stage3_9c_equivalent_odb(
    stage3_9b_dir: str | Path = STAGE3_9B_DIR,
    out_dir: str | Path = STAGE3_9C_DIR,
    equivalent_odb: str | Path = POWER_2X_ODB,
    reference_odb: str | Path = POWER_1X_ODB,
    runtime_config: str | Path = RUNTIME_CONFIG,
) -> dict[str, Any]:
    source_dir = Path(stage3_9b_dir)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate_odb = Path(equivalent_odb)
    base_odb = Path(reference_odb)

    preconditions = verify_stage3_9c_preconditions(source_dir, candidate_odb)
    if not preconditions["ok"]:
        summary = _blocked_summary(target_dir, preconditions)
        _write_all_stage_artifacts(target_dir, summary, {}, {}, {}, {}, summary)
        return _result(summary, target_dir, success=False)

    intake_request = {
        "stage": "Stage 3.9C",
        "input_mode": "manual_equivalent_odb",
        "equivalence_basis": "Stage 3.9B real sanity-base-derived candidate evidence",
        "stage3_9b_dir": str(source_dir),
        "candidate_inp_path": preconditions["candidate_inp_path"],
        "requested_odb_path": str(candidate_odb),
        "reference_odb_path": str(base_odb),
    }
    intake_result = {
        **intake_request,
        "accepted_odb_path": str(candidate_odb),
        "odb_exists": candidate_odb.exists(),
        "lock_exists": _lock_exists(candidate_odb),
        "output_accepted": True,
        "opened_odb": False,
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
    }
    intake_summary = dict(intake_result)

    contract = _build_contract(base_odb, candidate_odb)
    contract_path = target_dir / "equivalent_odb_metrics_contract.json"
    _write_json(contract_path, contract)
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
    gated_dir = target_dir / "gated_odb_metrics"
    metrics_request = extractor.prepare_request(contract_path, gated_dir)
    metrics_result = extractor.extract(metrics_request)
    metrics_path = Path(str(metrics_request.get("metrics_json_path", "")))
    metrics_payload = _read_json(metrics_path) if metrics_path.exists() else {}
    metrics_summary = {
        "stage": "Stage 3.9C",
        "metrics_status": (
            "EQUIVALENT_ODB_METRICS_READY"
            if metrics_result.get("verdict") == "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY"
            else metrics_result.get("verdict", "EQUIVALENT_ODB_METRICS_FAILED")
        ),
        "metrics_available": bool(metrics_payload),
        "metrics_json_path": str(metrics_path) if metrics_path else None,
        "gated_extractor_verdict": metrics_result.get("verdict"),
        "extractor_executed": bool(metrics_result.get("executed")),
        "opened_odb_only_via_gated_extractor": bool(metrics_result.get("executed")),
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
        "opened_odb_directly": False,
        "key_metrics": _key_metrics(metrics_payload),
        "errors": list(metrics_result.get("errors", [])),
    }

    report = _build_report(target_dir, preconditions, intake_result, metrics_summary, metrics_payload)
    smoke_summary = {
        "schema_version": "0.1",
        "stage": "Stage 3.9C",
        "verdict": (
            "PASS_ABQPILOT_V2_STAGE3_9C_EQUIVALENT_REAL_ODB_INTAKE_METRICS_REPORT_READY"
            if report["patched_metrics_available"]
            else "PASS_STAGE3_9C_AGENTS_RULE_ADDED_EQUIVALENT_ODB_INTAKE_READY_METRICS_BLOCKED_SAFE"
        ),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_inp_path": preconditions["candidate_inp_path"],
        "accepted_odb_path": str(candidate_odb),
        "reference_odb_path": str(base_odb),
        "odb_exists": candidate_odb.exists(),
        "lock_exists": _lock_exists(candidate_odb),
        "output_accepted": True,
        "patched_metrics_available": report["patched_metrics_available"],
        "reference_metrics_available": report["reference_metrics_available"],
        "comparison_available": report["comparison_available"],
        "evaluation_verdict": report["evaluation_verdict"],
        "report_written": True,
        "opened_odb_only_via_gated_extractor": metrics_summary["opened_odb_only_via_gated_extractor"],
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
        "mutated_queue_json": False,
        "opened_odb_directly": False,
        "preconditions": preconditions,
        "key_metrics": metrics_summary["key_metrics"],
    }
    _write_all_stage_artifacts(
        target_dir,
        intake_request,
        intake_result,
        intake_summary,
        metrics_request,
        metrics_result,
        metrics_summary,
        report,
        smoke_summary,
    )
    return _result(smoke_summary, target_dir, success=smoke_summary["verdict"].startswith("PASS_ABQPILOT"))


def verify_stage3_9c_preconditions(stage3_9b_dir: str | Path, equivalent_odb: str | Path = POWER_2X_ODB) -> dict[str, Any]:
    root = Path(stage3_9b_dir)
    summary = _read_json(root / "real_sanity_base_patch_candidate_summary.json")
    diff = _read_json(root / "patch_diff_report.json")
    static = _read_json(root / "static_validation_report.json")
    physics = _read_json(root / "physics_guard_report.json")
    candidate = Path(str(summary.get("candidate_inp_path") or root / "candidate_sanity_base_power_x2.inp"))
    source = Path(str(summary.get("source_inp_path") or root / "source_sanity_base_export.inp"))
    odb = Path(equivalent_odb)
    checks = {
        "candidate_exists": candidate.exists(),
        "candidate_sha256_matches_summary": candidate.exists()
        and summary.get("candidate_inp_sha256") == sha256_file(str(candidate)),
        "candidate_heat_flux_2x": candidate.exists() and CANDIDATE_HEAT_LINE in candidate.read_text(encoding="utf-8", errors="replace"),
        "source_heat_flux_1x": source.exists() and SOURCE_HEAT_LINE in source.read_text(encoding="utf-8", errors="replace"),
        "changed_lines_count_is_one": summary.get("changed_lines_count") == 1 or len(diff.get("changed_lines", [])) == 1,
        "unrelated_changes_count_zero": summary.get("unrelated_changes_count") == 0,
        "static_validator_pass": summary.get("static_validator_status") == "PASS" or static.get("passed") is True,
        "diff_guard_pass": summary.get("diff_guard_status") == "PASS" or diff.get("allowed") is True,
        "physics_guard_pass": summary.get("physics_guard_status") == "PASS" or physics.get("passed") is True,
        "equivalent_odb_exists": odb.exists(),
        "equivalent_odb_unlocked": odb.exists() and not _lock_exists(odb),
        "equivalence_yes": summary.get("existing_power_2x_odb_equivalent_candidate_output") == "YES",
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "summary_path": str(root / "real_sanity_base_patch_candidate_summary.json"),
        "candidate_inp_path": str(candidate),
        "source_inp_path": str(source),
        "equivalent_odb_path": str(odb),
        "warning_verdict": None if all(checks.values()) else "WARNING_STAGE3_9C_EQUIVALENT_ODB_INTAKE_PRECONDITION_FAILED",
    }


def _build_contract(reference_odb: Path, equivalent_odb: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "cases": [
            {"case_id": "base_power_1x", "role": "base", "odb_path": str(reference_odb)},
            {"case_id": "equivalent_power_x2", "role": "power_x2", "odb_path": str(equivalent_odb)},
        ],
        "temperature_field_candidates": ["NT11", "NT"],
        "stress_field": "S",
        "heated_region_status": "TARGET_REGION_NOT_CONFIRMED",
        "frame_selection": {"preferred": "last_frame", "cooling_time_s": 100.0},
        "metrics": ["NT_max", "NT_mean_global", "S_Mises_max", "S_Mises_mean_global"],
        "default_behavior": "gated_metrics_only_no_solver_submit",
    }


def _build_report(
    target_dir: Path,
    preconditions: dict[str, Any],
    intake_result: dict[str, Any],
    metrics_summary: dict[str, Any],
    metrics_payload: dict[str, Any],
) -> dict[str, Any]:
    base_case = _case_by_role(metrics_payload, "base")
    x2_case = _case_by_role(metrics_payload, "power_x2")
    base_metrics = base_case.get("metrics", {}) if base_case else {}
    x2_metrics = x2_case.get("metrics", {}) if x2_case else {}
    comparison = _comparison(base_metrics, x2_metrics)
    reference_available = bool(base_metrics)
    patched_available = bool(x2_metrics)
    comparison_available = bool(comparison)
    verdict = _evaluation_verdict(comparison, reference_available, patched_available)
    report = {
        "schema_version": "0.1",
        "stage": "Stage 3.9C",
        "evaluation_verdict": verdict,
        "candidate_traceability": "sanity-base-derived",
        "source_heat_flux": "1e+10",
        "candidate_heat_flux": "2e+10",
        "candidate_inp_path": preconditions["candidate_inp_path"],
        "accepted_odb_path": intake_result["accepted_odb_path"],
        "patched_metrics_available": patched_available,
        "reference_metrics_available": reference_available,
        "comparison_available": comparison_available,
        "base_metrics": base_metrics,
        "patched_metrics": x2_metrics,
        "comparison": comparison,
        "field_temperature": x2_case.get("temperature_field_used") if x2_case else None,
        "opened_odb_only_via_gated_extractor": metrics_summary["opened_odb_only_via_gated_extractor"],
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
        "opened_odb_directly": False,
        "artifact_dir": str(target_dir),
    }
    return report


def _evaluation_verdict(comparison: dict[str, Any], reference_available: bool, patched_available: bool) -> str:
    if not patched_available:
        return "INSUFFICIENT_REFERENCE"
    if not reference_available or not comparison:
        return "INSUFFICIENT_REFERENCE"
    nt_delta = comparison.get("NT_max_delta")
    stress_delta = comparison.get("S_Mises_max_delta")
    if nt_delta is not None and stress_delta is not None and nt_delta > 0 and stress_delta < 0:
        return "EQUIVALENT_PATCHED_MIXED"
    if nt_delta is not None and stress_delta is not None and nt_delta > 0 and stress_delta <= 0:
        return "EQUIVALENT_PATCHED_IMPROVED"
    if nt_delta is not None and nt_delta <= 0:
        return "EQUIVALENT_PATCHED_REGRESSED"
    return "EQUIVALENT_PATCHED_METRICS_READY"


def _comparison(base_metrics: dict[str, Any], x2_metrics: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ["NT_max", "NT_mean_global", "S_Mises_max", "S_Mises_mean_global"]:
        base = base_metrics.get(key)
        x2 = x2_metrics.get(key)
        if isinstance(base, (int, float)) and isinstance(x2, (int, float)):
            result[f"{key}_delta"] = x2 - base
            result[f"{key}_ratio"] = None if base == 0 else x2 / base
    return result


def _key_metrics(metrics_payload: dict[str, Any]) -> dict[str, Any]:
    x2 = _case_by_role(metrics_payload, "power_x2")
    base = _case_by_role(metrics_payload, "base")
    return {
        "base": base.get("metrics", {}) if base else {},
        "patched": x2.get("metrics", {}) if x2 else {},
        "field_temperature": x2.get("temperature_field_used") if x2 else None,
    }


def _case_by_role(metrics_payload: dict[str, Any], role: str) -> dict[str, Any]:
    for case in metrics_payload.get("cases", []):
        if case.get("role") == role:
            return case
    return {}


def _blocked_summary(target_dir: Path, preconditions: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 3.9C",
        "verdict": "WARNING_STAGE3_9C_EQUIVALENT_ODB_INTAKE_PRECONDITION_FAILED",
        "artifact_dir": str(target_dir),
        "preconditions": preconditions,
        "output_accepted": False,
        "patched_metrics_available": False,
        "report_written": False,
        "opened_odb_only_via_gated_extractor": False,
        "submitted_solver": False,
        "queue_runner_launched": False,
        "created_new_queue_job": False,
        "mutated_queue_json": False,
        "opened_odb_directly": False,
    }


def _write_all_stage_artifacts(
    target_dir: Path,
    intake_request: dict[str, Any],
    intake_result: dict[str, Any],
    intake_summary: dict[str, Any],
    metrics_request: dict[str, Any],
    metrics_result: dict[str, Any],
    metrics_summary: dict[str, Any],
    report: dict[str, Any] | None = None,
    smoke_summary: dict[str, Any] | None = None,
) -> None:
    report = report or {}
    smoke_summary = smoke_summary or {}
    _write_json(target_dir / "equivalent_odb_intake_request.json", intake_request)
    _write_json(target_dir / "equivalent_odb_intake_result.json", intake_result)
    _write_json(target_dir / "equivalent_odb_intake_summary.json", intake_summary)
    _write_text(target_dir / "equivalent_odb_intake_summary.md", _render_intake_md(intake_summary))
    _write_json(target_dir / "equivalent_odb_metrics_request.json", metrics_request)
    _write_json(target_dir / "equivalent_odb_metrics_result.json", metrics_result)
    _write_json(target_dir / "equivalent_odb_metrics_summary.json", metrics_summary)
    _write_text(target_dir / "equivalent_odb_metrics_summary.md", _render_metrics_md(metrics_summary))
    _write_json(target_dir / "equivalent_odb_report.json", report)
    _write_text(target_dir / "equivalent_odb_report.md", _render_report_md(report))
    _write_json(target_dir / "stage3_9c_equivalent_real_odb_smoke_summary.json", smoke_summary)
    _write_text(target_dir / "stage3_9c_equivalent_real_odb_smoke_summary.md", _render_smoke_md(smoke_summary))


def _render_intake_md(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Stage 3.9C Equivalent ODB Intake",
            "",
            f"Output accepted: `{summary.get('output_accepted')}`",
            f"Accepted ODB: `{summary.get('accepted_odb_path')}`",
            f"Lock exists: `{summary.get('lock_exists')}`",
            "",
            "No solver was submitted. No queue job was created. ODB was not opened by intake.",
        ]
    ) + "\n"


def _render_metrics_md(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Stage 3.9C Equivalent ODB Metrics",
            "",
            f"Metrics status: `{summary.get('metrics_status')}`",
            f"Gated extractor verdict: `{summary.get('gated_extractor_verdict')}`",
            f"Metrics available: `{summary.get('metrics_available')}`",
            f"Opened ODB only via gated extractor: `{summary.get('opened_odb_only_via_gated_extractor')}`",
        ]
    ) + "\n"


def _render_report_md(report: dict[str, Any]) -> str:
    patched = report.get("patched_metrics", {})
    base = report.get("base_metrics", {})
    return "\n".join(
        [
            "# Stage 3.9C Equivalent Real ODB Report",
            "",
            f"Verdict: `{report.get('evaluation_verdict')}`",
            f"Candidate traceability: `{report.get('candidate_traceability')}`",
            f"Source heat flux: `{report.get('source_heat_flux')}`",
            f"Candidate heat flux: `{report.get('candidate_heat_flux')}`",
            "",
            "## Key Metrics",
            "",
            f"- Base NT_max: `{base.get('NT_max')}`",
            f"- Equivalent 2x NT_max: `{patched.get('NT_max')}`",
            f"- Base S_Mises_max: `{base.get('S_Mises_max')}`",
            f"- Equivalent 2x S_Mises_max: `{patched.get('S_Mises_max')}`",
            "",
            "No solver was submitted. No queue job was created. ODB access was limited to the existing gated extractor.",
        ]
    ) + "\n"


def _render_smoke_md(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Stage 3.9C Equivalent Real ODB Smoke",
            "",
            f"Verdict: `{summary.get('verdict')}`",
            f"Accepted ODB: `{summary.get('accepted_odb_path')}`",
            f"Evaluation verdict: `{summary.get('evaluation_verdict')}`",
            f"Submitted solver: `{summary.get('submitted_solver')}`",
            f"Created new queue job: `{summary.get('created_new_queue_job')}`",
            f"Opened ODB directly: `{summary.get('opened_odb_directly')}`",
        ]
    ) + "\n"


def _result(summary: dict[str, Any], target_dir: Path, success: bool) -> dict[str, Any]:
    return {
        "command": "run-stage3-9c-equivalent-odb",
        "verdict": summary.get("verdict"),
        "success": bool(success),
        "output_paths": {
            "artifact_dir": str(target_dir),
            "intake_summary": str(target_dir / "equivalent_odb_intake_summary.json"),
            "metrics_summary": str(target_dir / "equivalent_odb_metrics_summary.json"),
            "report_json": str(target_dir / "equivalent_odb_report.json"),
            "smoke_summary": str(target_dir / "stage3_9c_equivalent_real_odb_smoke_summary.json"),
        },
        "details": summary,
        "errors": [] if success else [summary.get("verdict", "Stage 3.9C failed")],
        "warnings": [],
    }


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


def _lock_exists(path: Path) -> bool:
    return path.with_suffix(".lck").exists() or Path(str(path) + ".lck").exists()


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
