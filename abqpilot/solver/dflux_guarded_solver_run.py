from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file, sha256_json_obj
from abqpilot.solver.controlled_abaqus_runner import execute_controlled_abaqus_command
from abqpilot.solver.solver_artifacts import read_json, result, tail_text, timestamp, write_json, write_text
from abqpilot.solver.solver_monitor import classify_solver_run
from abqpilot.solver.solver_report import intake_solver_run_output, report_solver_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGE4_4_ROOT = PROJECT_ROOT / "runs" / "stage4_4_dflux_deactivated_controlled_solver_validation"
DEFAULT_ABAQUS_COMMAND = r"D:\ABAQUS2024\Commands\abq2024.bat"
DFLUX_APPROVAL_PHRASE = "I_APPROVE_ABQPILOT_DFLUX_DEACTIVATED_CONTROLLED_SOLVER_RUN"
DFLUX_APPROVAL_TYPE = "abqpilot_dflux_deactivated_controlled_solver_run"
DFLUX_JOB_NAME = "candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver"
DFLUX_LOCAL_INP = f"{DFLUX_JOB_NAME}.inp"


REQUIRED_GUARD_VALUES = {
    "static_validator": "PASS",
    "diff_guard": "PASS",
    "physics_guard": "PASS",
    "dflux_lifecycle_validator": "PASS",
    "source_inp_unchanged": True,
    "preview_inp_created": True,
    "cooling_step_has_dflux_op_new": True,
    "cooling_step_positive_bf_lines": 0,
    "scan_step_bf_preserved": True,
    "unrelated_changes_count": 0,
}


def prepare_dflux_guarded_solver_run(
    preview_inp: str | Path,
    validation_json: str | Path,
    output_root: str | Path = DEFAULT_STAGE4_4_ROOT,
    cpus: int = 14,
    abaqus_command: str | Path = DEFAULT_ABAQUS_COMMAND,
) -> dict[str, Any]:
    preview = Path(preview_inp)
    validation_path = Path(validation_json)
    validation = read_json(validation_path)
    run_dir = Path(output_root) / ("run_" + timestamp())
    run_dir.mkdir(parents=True, exist_ok=False)
    solver_inp = run_dir / DFLUX_LOCAL_INP
    eligibility = _build_eligibility(preview, solver_inp, validation_path, validation, run_dir, int(cpus), abaqus_command)
    write_json(run_dir / "dflux_guarded_solver_eligibility.json", eligibility)

    if eligibility["dflux_lifecycle_guard"] != "PASS":
        write_json(run_dir / "dflux_guarded_solver_prepare.json", eligibility)
        return result("prepare-dflux-guarded-solver-run", "DFLUX_LIFECYCLE_GUARD_BLOCKED_SOLVER_RUN", False, run_dir, eligibility)

    shutil.copyfile(preview, solver_inp)
    eligibility["solver_inp_sha256"] = sha256_file(solver_inp)
    eligibility["solver_inp"] = str(solver_inp)
    eligibility["copied_preview_inp_unchanged"] = sha256_file(preview) == eligibility["preview_inp_sha256"]

    command_preview = _command_preview(abaqus_command, DFLUX_JOB_NAME, DFLUX_LOCAL_INP, int(cpus))
    command_payload = {"command": command_preview}
    command_hash = sha256_json_obj(command_payload)
    preflight = {
        **eligibility,
        "stage": "Stage 4.4",
        "solver_run_dir": str(run_dir),
        "job_name": DFLUX_JOB_NAME,
        "expected_odb_path": str(run_dir / f"{DFLUX_JOB_NAME}.odb"),
        "cpus": int(cpus),
        "command_preview": command_preview,
        "command_preview_text": " ".join(f'"{x}"' if " " in str(x) else str(x) for x in command_preview),
        "abaqus_command_preview_sha256": command_hash,
        "eligible_for_solver_after_human_approval": True,
        "solver_run_allowed_without_approval": False,
        "requires_human_approval": True,
        "queue_runner_launched": False,
        "abqjobpilot_gui_launched": False,
        "llm_execution_authority": False,
        "errors": [],
        "warnings": [],
    }
    approval_request = _approval_request(preflight)
    write_json(run_dir / "dflux_guarded_solver_eligibility.json", eligibility)
    write_json(run_dir / "dflux_guarded_solver_prepare.json", preflight)
    write_json(run_dir / "dflux_guarded_solver_command_preview.json", command_payload)
    write_json(run_dir / "solver_preflight_result.json", preflight)
    write_json(run_dir / "solver_command_preview.json", command_payload)
    write_text(run_dir / "solver_command_preview.txt", preflight["command_preview_text"] + "\n")
    write_json(run_dir / "dflux_guarded_solver_approval_request.json", approval_request)
    write_json(run_dir / "solver_approval_request.json", approval_request)
    return result("prepare-dflux-guarded-solver-run", "DFLUX_GUARDED_SOLVER_RUN_PREPARED", True, run_dir, preflight)


def approve_dflux_guarded_solver_run(
    solver_run_dir: str | Path,
    approval_phrase: str,
    approved_by: str = "human",
    expires_hours: int | float = 24,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    request = read_json(run_dir / "dflux_guarded_solver_approval_request.json")
    if approval_phrase != DFLUX_APPROVAL_PHRASE:
        details = {"approval_status": "APPROVAL_TOKEN_INVALID", "errors": ["approval phrase does not match required phrase"], "warnings": []}
        return result("approve-dflux-guarded-solver-run", "APPROVAL_TOKEN_INVALID", False, run_dir, details)
    valid, errors = _approval_request_is_safe(request)
    if not valid:
        details = {"approval_status": "APPROVAL_UNSAFE_CONDITIONS", "errors": errors, "warnings": []}
        return result("approve-dflux-guarded-solver-run", "APPROVAL_UNSAFE_CONDITIONS", False, run_dir, details)
    created_at = datetime.now()
    token = {
        "schema_version": "0.1",
        "stage": "Stage 4.4",
        "approval_type": DFLUX_APPROVAL_TYPE,
        "approved_step": "dflux_deactivated_controlled_solver_run",
        "approved_by": approved_by,
        "approval_phrase": approval_phrase,
        "created_at": created_at.isoformat(timespec="seconds"),
        "expires_at": (created_at + timedelta(hours=float(expires_hours))).isoformat(timespec="seconds"),
    }
    for field in _approval_bound_fields():
        token[field] = request.get(field)
    token_path = run_dir / "approvals" / "dflux_guarded_solver_approval_token.json"
    write_json(token_path, token)
    write_json(run_dir / "dflux_guarded_solver_approval_token.json", token)
    details = {"approval_status": "DFLUX_GUARDED_SOLVER_APPROVAL_TOKEN_CREATED", "approval_token_path": str(token_path), "errors": [], "warnings": []}
    return result("approve-dflux-guarded-solver-run", "DFLUX_GUARDED_SOLVER_APPROVAL_TOKEN_CREATED", True, run_dir, details)


def run_dflux_guarded_solver_approved(
    solver_run_dir: str | Path,
    approval_token: str | Path | None = None,
    timeout_s: int = 7200,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    validation = validate_dflux_approval_token(run_dir, approval_token)
    if not validation["valid"]:
        details = {
            "solver_launched": False,
            "approval_status": validation["status"],
            "errors": validation.get("errors", []),
            "queue_runner_launched": False,
            "abqjobpilot_gui_launched": False,
            "llm_execution_authority": False,
            "odb_opened": False,
        }
        write_json(run_dir / "dflux_guarded_solver_run_result.json", details)
        return result("run-dflux-guarded-solver-approved", "DFLUX_GUARDED_SOLVER_BLOCKED_APPROVAL_REQUIRED", False, run_dir, details)

    preflight = read_json(run_dir / "dflux_guarded_solver_prepare.json")
    command = _command_preview(preflight["command_preview"][0], preflight["job_name"], DFLUX_LOCAL_INP, int(preflight["cpus"]))
    if command != preflight.get("command_preview"):
        details = {
            "solver_launched": False,
            "errors": ["command preview does not match fixed DFLUX command structure"],
            "queue_runner_launched": False,
            "abqjobpilot_gui_launched": False,
            "llm_execution_authority": False,
            "odb_opened": False,
        }
        write_json(run_dir / "dflux_guarded_solver_run_result.json", details)
        return result("run-dflux-guarded-solver-approved", "DFLUX_GUARDED_SOLVER_BLOCKED_UNSAFE_COMMAND", False, run_dir, details)

    request = {"stage": "Stage 4.4", "solver_run_dir": str(run_dir), "command": command, "cwd": str(run_dir), "shell": False, "timeout_s": timeout_s}
    write_json(run_dir / "dflux_guarded_solver_run_request.json", request)
    run_report: dict[str, Any] = {
        **request,
        "solver_launched": True,
        "solver_run": True,
        "queue_runner_launched": False,
        "abqjobpilot_gui_launched": False,
        "llm_execution_authority": False,
        "odb_opened": False,
        "return_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "expected_odb_path": preflight.get("expected_odb_path"),
        "expected_odb_exists": False,
        "lock_exists_after_completion": False,
        "errors": [],
    }
    execution = execute_controlled_abaqus_command(command, run_dir, timeout_s)
    run_report.update(execution)
    run_report["solver_run"] = bool(run_report.get("solver_launched"))

    monitor = classify_solver_run(run_dir)
    run_report["monitor_status"] = monitor["status"]
    run_report["diagnosis_status"] = monitor.get("diagnosis_status")
    run_report["odb_acceptable_for_metrics"] = monitor.get("odb_acceptable_for_metrics")
    run_report["expected_odb_exists"] = bool(monitor.get("odb_exists"))
    run_report["lock_exists_after_completion"] = bool(monitor.get("lock_exists"))
    run_report["sta_tail"] = tail_text(run_dir / f"{DFLUX_JOB_NAME}.sta")
    run_report["msg_tail"] = tail_text(run_dir / f"{DFLUX_JOB_NAME}.msg")
    run_report["dat_tail"] = tail_text(run_dir / f"{DFLUX_JOB_NAME}.dat")
    verdict = "CONTROLLED_SOLVER_RUN_COMPLETED" if run_report.get("return_code") == 0 and monitor["status"] == "SOLVER_COMPLETED" else "CONTROLLED_SOLVER_RUN_FAILED"
    write_json(run_dir / "dflux_guarded_solver_run_result.json", run_report)
    write_json(run_dir / "solver_run_result.json", run_report)
    return result("run-dflux-guarded-solver-approved", verdict, verdict == "CONTROLLED_SOLVER_RUN_COMPLETED", run_dir, run_report)


def monitor_dflux_guarded_solver_run(solver_run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    monitor = classify_solver_run(run_dir)
    write_json(run_dir / "dflux_guarded_solver_monitor.json", monitor)
    return result("monitor-dflux-guarded-solver-run", monitor["status"], True, run_dir, monitor)


def intake_dflux_guarded_solver_output(solver_run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    intake = intake_solver_run_output(run_dir)
    details = {**intake.get("details", {}), "stage": "Stage 4.4"}
    write_json(run_dir / "dflux_guarded_solver_intake.json", details)
    verdict = "DFLUX_GUARDED_SOLVER_OUTPUT_ACCEPTED" if details.get("solver_output_accepted") else "DFLUX_GUARDED_SOLVER_OUTPUT_NOT_READY"
    return result("intake-dflux-guarded-solver-output", verdict, bool(details.get("solver_output_accepted")), run_dir, details)


def report_dflux_guarded_solver_run(solver_run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    report = report_solver_run(run_dir)
    details = {**report.get("details", {}), "stage": "Stage 4.4"}
    metrics = read_json(run_dir / "solver_metrics_result.json")
    write_json(run_dir / "dflux_guarded_solver_metrics.json", metrics or details)
    write_json(run_dir / "dflux_guarded_solver_comparison.json", details)
    write_text(run_dir / "dflux_guarded_solver_report.md", _render_stage4_4_report(details))
    return result("report-dflux-guarded-solver-run", details.get("evaluation_verdict") or details.get("verdict", report.get("verdict")), report.get("success", False), run_dir, details)


def validate_dflux_approval_token(solver_run_dir: str | Path, token_path: str | Path | None = None) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    request = read_json(run_dir / "dflux_guarded_solver_approval_request.json")
    safe, errors = _approval_request_is_safe(request)
    if not safe:
        return {"status": "APPROVAL_UNSAFE_CONDITIONS", "valid": False, "errors": errors}
    token_file = Path(token_path) if token_path else run_dir / "approvals" / "dflux_guarded_solver_approval_token.json"
    if not token_file.exists():
        return {"status": "APPROVAL_TOKEN_MISSING", "valid": False, "errors": ["approval token is missing"]}
    token = read_json(token_file)
    if token.get("approval_type") != DFLUX_APPROVAL_TYPE or token.get("approval_phrase") != DFLUX_APPROVAL_PHRASE:
        return {"status": "APPROVAL_TOKEN_INVALID", "valid": False, "errors": ["approval token type or phrase is invalid"]}
    try:
        expires_at = datetime.fromisoformat(str(token.get("expires_at")))
    except ValueError:
        return {"status": "APPROVAL_TOKEN_INVALID", "valid": False, "errors": ["approval token expires_at is invalid"]}
    if expires_at <= datetime.now():
        return {"status": "APPROVAL_TOKEN_EXPIRED", "valid": False, "errors": ["approval token is expired"]}
    mismatches = [field for field in _approval_bound_fields() if token.get(field) != request.get(field)]
    preview = Path(str(request.get("preview_inp", "")))
    solver = Path(str(request.get("solver_inp", "")))
    if preview.exists() and sha256_file(preview) != request.get("preview_inp_sha256"):
        mismatches.append("preview_file_current_sha256")
    if solver.exists() and sha256_file(solver) != request.get("solver_inp_sha256"):
        mismatches.append("solver_file_current_sha256")
    if mismatches:
        return {"status": "APPROVAL_HASH_MISMATCH", "valid": False, "errors": [f"mismatch: {field}" for field in mismatches]}
    return {"status": "APPROVAL_TOKEN_VALID", "valid": True, "token_path": str(token_file), "errors": []}


def _build_eligibility(
    preview: Path,
    solver_inp: Path,
    validation_path: Path,
    validation: dict[str, Any],
    run_dir: Path,
    cpus: int,
    abaqus_command: str | Path,
) -> dict[str, Any]:
    errors: list[str] = []
    if not preview.exists():
        errors.append("preview INP is missing")
    if not validation_path.exists():
        errors.append("DFLUX lifecycle validation JSON is missing")
    guard_errors = [key for key, expected in REQUIRED_GUARD_VALUES.items() if validation.get(key) != expected]
    errors.extend([f"{key} must be {expected!r}" for key, expected in REQUIRED_GUARD_VALUES.items() if validation.get(key) != expected])
    if cpus < 1 or cpus > 14:
        errors.append("cpus must be between 1 and 14")
    dflux_guard = "PASS" if not guard_errors and preview.exists() and validation_path.exists() and 1 <= cpus <= 14 else "FAIL"
    return {
        "schema_version": "0.1",
        "stage": "Stage 4.4",
        "preview_inp": str(preview),
        "preview_inp_sha256": sha256_file(preview) if preview.exists() else None,
        "solver_inp": str(solver_inp),
        "solver_inp_sha256": None,
        "validation_json": str(validation_path),
        "dflux_lifecycle_validation_sha256": sha256_file(validation_path) if validation_path.exists() else None,
        "solver_run_dir": str(run_dir),
        "job_name": DFLUX_JOB_NAME,
        "expected_odb_path": str(run_dir / f"{DFLUX_JOB_NAME}.odb"),
        "cpus": cpus,
        "abaqus_command": str(abaqus_command),
        "dflux_lifecycle_guard": dflux_guard,
        "mcp_guard_subcheck": "MCPGuard.load_lifecycle.body_heat_flux_dflux_bf",
        "mcp_guard_required_for_future_solver_eligibility": True,
        "static_validator": validation.get("static_validator"),
        "diff_guard": validation.get("diff_guard"),
        "physics_guard": validation.get("physics_guard"),
        "dflux_lifecycle_validator": validation.get("dflux_lifecycle_validator"),
        "source_inp_unchanged": validation.get("source_inp_unchanged"),
        "preview_inp_created": validation.get("preview_inp_created"),
        "cooling_step_has_dflux_op_new": validation.get("cooling_step_has_dflux_op_new"),
        "cooling_step_positive_bf_lines": validation.get("cooling_step_positive_bf_lines"),
        "scan_step_bf_preserved": validation.get("scan_step_bf_preserved"),
        "unrelated_changes_count": validation.get("unrelated_changes_count"),
        "eligible_for_solver_after_human_approval": dflux_guard == "PASS",
        "solver_run_allowed_without_approval": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "errors": errors,
        "warnings": [],
    }


def _approval_request(preflight: dict[str, Any]) -> dict[str, Any]:
    request = {
        "schema_version": "0.1",
        "stage": "Stage 4.4",
        "approval_type": DFLUX_APPROVAL_TYPE,
        "status": "APPROVAL_REQUIRED",
        "required_phrase": DFLUX_APPROVAL_PHRASE,
    }
    for field in _approval_bound_fields():
        request[field] = preflight.get(field)
    request["required_conditions"] = {
        "dflux_lifecycle_guard": "PASS",
        "queue_runner_allowed": False,
        "abqjobpilot_gui_allowed": False,
        "llm_execution_authority": False,
        "uncontrolled_odb_open_allowed": False,
    }
    return request


def _approval_bound_fields() -> list[str]:
    return [
        "preview_inp",
        "preview_inp_sha256",
        "solver_inp",
        "solver_inp_sha256",
        "validation_json",
        "dflux_lifecycle_validation_sha256",
        "dflux_lifecycle_guard",
        "static_validator",
        "diff_guard",
        "physics_guard",
        "dflux_lifecycle_validator",
        "source_inp_unchanged",
        "preview_inp_created",
        "cooling_step_has_dflux_op_new",
        "cooling_step_positive_bf_lines",
        "scan_step_bf_preserved",
        "unrelated_changes_count",
        "abaqus_command_preview_sha256",
        "command_preview",
        "job_name",
        "cpus",
        "expected_odb_path",
        "solver_run_dir",
        "solver_run_allowed_without_approval",
    ]


def _approval_request_is_safe(request: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not request:
        return False, ["DFLUX guarded solver approval request is missing"]
    if request.get("dflux_lifecycle_guard") != "PASS":
        errors.append("DFLUX lifecycle guard must pass")
    for key, expected in REQUIRED_GUARD_VALUES.items():
        if request.get(key) != expected:
            errors.append(f"{key} must be {expected!r}")
    if request.get("required_conditions", {}).get("queue_runner_allowed") is not False:
        errors.append("QueueRunner must not be allowed")
    if request.get("required_conditions", {}).get("llm_execution_authority") is not False:
        errors.append("LLM execution authority must be false")
    if request.get("solver_run_allowed_without_approval") is not False:
        errors.append("solver_run_allowed_without_approval must be false")
    return not errors, errors


def _command_preview(abaqus_command: str | Path, job_name: str, input_name: str, cpus: int) -> list[str]:
    if job_name != DFLUX_JOB_NAME or input_name != DFLUX_LOCAL_INP:
        raise ValueError("Stage 4.4 command must use fixed DFLUX job and input names")
    if cpus < 1 or cpus > 14:
        raise ValueError("cpus must be between 1 and 14")
    return [str(abaqus_command), f"job={job_name}", f"input={input_name}", f"cpus={cpus}", "interactive"]


def _render_stage4_4_report(details: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Stage 4.4 DFLUX-Guarded Solver Report",
            "",
            f"Verdict: `{details.get('evaluation_verdict') or details.get('verdict')}`",
            f"Solver metrics available: `{details.get('solver_metrics_available')}`",
            f"Reference metrics available: `{details.get('reference_metrics_available')}`",
            f"Comparison available: `{details.get('comparison_available')}`",
            f"Opened ODB only via gated extractor: `{details.get('opened_odb_only_via_gated_extractor')}`",
            "",
            "The DFLUX lifecycle guard is required before solver launch. QueueRunner and LLM execution authority remain disabled.",
        ]
    ) + "\n"
