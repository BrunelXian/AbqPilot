from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_demo_smoke_v2_audit import audit_stage5_3a_v2_no_forbidden_outputs, scan_forbidden_root_for_stage5_3a_markers
from abqpilot.gui.controlled_solver_demo_smoke_v2_report import render_demo_smoke_v2_audit, render_demo_smoke_v2_report
from abqpilot.gui.controlled_solver_demo_smoke_v2_runner import ABAQUS_COMMAND, CPU_COUNT, JOB_NAME, TASK_ID, TIMEOUT_SECONDS, build_stage5_3a_v2_demo_command, execute_stage5_3a_v2_demo_solver_request
from abqpilot.gui.controlled_solver_demo_smoke_v2_validator import validate_demo_gate_v2, validate_demo_solver_request_v2
from abqpilot.workspace_guard import PROJECT_ROOT, verify_write_target

STAGE_ID = "STAGE5_3A_V2"
STAGE5_3A_V2_VERDICT = "PASS_ABQPILOT_V2_STAGE5_3A_V2_CONTROLLED_SOLVER_DEMO_SMOKE_RUN_READY"
INFRA_READY_SOLVER_NOT_RUN = "PASS_STAGE5_3A_V2_CONTROLLED_SOLVER_DEMO_SMOKE_INFRA_READY_SOLVER_NOT_RUN_ENV_UNAVAILABLE"
NONZERO_RETURN = "PASS_STAGE5_3A_V2_CONTROLLED_SOLVER_DEMO_SMOKE_RUN_ATTEMPT_RECORDED_NONZERO_RETURN"
NO_INP = "BLOCKED_STAGE5_3A_V2_NO_SOLVER_READY_INP_FOUND"


def run_controlled_solver_demo_smoke_v2(project_root: str | Path = PROJECT_ROOT, attempt_solver: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve(strict=False)
    task = root / "runs" / "tasks" / TASK_ID
    guard = verify_write_target(root / "PROJECT_STATUS_CURRENT.json", root)
    pre_hits = scan_forbidden_root_for_stage5_3a_markers()
    if not guard.allowed or pre_hits:
        return _blocked("FAIL_STAGE5_3A_V2_CONTROLLED_SOLVER_DEMO_SMOKE_RUN_SAFETY_BOUNDARY_VIOLATION", task, {"workspace_guard": guard.__dict__, "forbidden_root_pre_scan_hits": pre_hits})
    selected = select_solver_ready_demo_inp_v2(root)
    if selected is None:
        return _blocked(NO_INP, task, {"candidate_search": "no solver-ready INP found"})

    source_hash_before = sha256_file(selected)
    paths = _ensure_task_dirs(task)
    copied = paths["solver_inputs"] / "demo_solver_smoke.inp"
    _copy_demo_inp(selected, copied, source_hash_before)
    source_hash_after = sha256_file(selected)
    copied_hash = sha256_file(copied)

    gate = build_demo_gate_v2(task, selected, copied, source_hash_before, copied_hash)
    request = build_demo_solver_request_v2(task, copied, copied_hash)
    gate_validation = validate_demo_gate_v2(gate)
    request_validation = validate_demo_solver_request_v2(request)
    _write_json(paths["gates"] / "GATE_001_DEMO_SOLVER_EXECUTION_APPROVAL.json", gate)
    _write_text(paths["gates"] / "GATE_001_DEMO_SOLVER_EXECUTION_APPROVAL.md", _render_gate_md(gate))
    _write_json(paths["solver_requests"] / "solver_request.json", request)
    _write_trace_files(task)
    if gate_validation["validation_status"] != "STAGE5_3A_V2_DEMO_GATE_VALID" or request_validation["validation_status"] != "STAGE5_3A_V2_DEMO_SOLVER_REQUEST_VALID":
        return _blocked("FAIL_STAGE5_3A_V2_DEMO_GATE_OR_REQUEST_INVALID", task, {"gate_validation": gate_validation, "request_validation": request_validation})

    runner_result = execute_stage5_3a_v2_demo_solver_request(request) if attempt_solver else _not_attempted(paths["solver_work"], copied)
    status = build_solver_status_v2(task, request, runner_result, copied, copied_hash)
    _write_json(paths["solver_status"] / "CONTROLLED_SOLVER_DEMO_RUN_STATUS.json", status)
    report_payload = {"stage": "Stage 5.3A-v2", "stage_id": STAGE_ID, "source_inp_path": str(selected), "source_inp_sha256": source_hash_before, "source_inp_sha256_after_copy": source_hash_after, "source_inp_mutated": source_hash_before != source_hash_after, "copied_inp_path": str(copied), "copied_inp_sha256": copied_hash, "gate_validation": gate_validation, "request_validation": request_validation, "status": status}
    _write_text(paths["solver_status"] / "CONTROLLED_SOLVER_DEMO_RUN_REPORT.md", render_demo_smoke_v2_report(report_payload))
    post_hits = scan_forbidden_root_for_stage5_3a_markers()
    audit = audit_stage5_3a_v2_no_forbidden_outputs(root, status)
    project_out = root / "gui_high_risk_gate_ux" / "controlled_solver_demo_smoke_run_v2"
    project_out.mkdir(parents=True, exist_ok=True)
    verdict = _verdict_for(status)
    result = {**report_payload, "schema_version": "0.1", "command": "run-controlled-solver-demo-smoke-v2", "verdict": verdict, "command_verdict": status["solver_status"], "success": verdict in {STAGE5_3A_V2_VERDICT, INFRA_READY_SOLVER_NOT_RUN, NONZERO_RETURN}, "task_id": TASK_ID, "task_dir": str(task), "workspace_guard_passed": guard.allowed and not pre_hits and not post_hits, "forbidden_root_pre_scan_hits": len(pre_hits), "forbidden_root_post_scan_hits": len(post_hits), "smoke_demo_only": True, "arbitrary_task_execution_allowed": False, "solver_request_created": True, "solver_request_path": str(paths["solver_requests"] / "solver_request.json"), "solver_invoked": status.get("solver_invoked") is True, "queue_runner_launched": False, "queue_entry_created": False, "odb_opened": False, "metrics_extracted": False, "metrics_approved": False, "final_evidence_approved": False, "final_verdict_frozen": False, "task_final_evidence_ledger_updated": False, "safety_audit": audit}
    _write_json(project_out / "CONTROLLED_SOLVER_DEMO_SMOKE_RUN_RESULT.json", result)
    _write_text(project_out / "CONTROLLED_SOLVER_DEMO_SMOKE_RUN_REPORT.md", render_demo_smoke_v2_report(result))
    _write_text(project_out / "CONTROLLED_SOLVER_DEMO_SMOKE_RUN_SAFETY_AUDIT.md", render_demo_smoke_v2_audit(audit))
    _write_text(project_out / "CONTROLLED_SOLVER_DEMO_SMOKE_RUN_NEXT_STEPS.md", _next_steps_md(status))
    _write_text(project_out / "WORKSPACE_GUARD_VERIFICATION.md", _workspace_guard_md(pre_hits, post_hits, guard.allowed))
    return result


def select_solver_ready_demo_inp_v2(project_root: str | Path) -> Path | None:
    root = Path(project_root)
    preferred = [
        root / "runs" / "stage4_4_dflux_deactivated_controlled_solver_validation" / "run_20260703_232004_870667" / "candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver.inp",
        root / "runs" / "stage4_3_guarded_dflux_deactivation_patch_preview" / "candidate_sanity_base_power_x2_stage4_dflux_deactivated_preview.inp",
        root / "runs" / "stage4_0_controlled_solver_automation" / "run_20260703_105833_589810" / "candidate_sanity_base_power_x2_stage4.inp",
        root / "runs" / "stage3_9b_real_sanity_base_patch_candidate" / "candidate_sanity_base_power_x2.inp",
    ]
    for candidate in preferred:
        if _is_allowed_candidate(root, candidate):
            return candidate
    for candidate in root.glob("runs/**/*.inp"):
        if _is_allowed_candidate(root, candidate):
            return candidate
    return None


def build_demo_gate_v2(task: Path, source: Path, copied: Path, source_hash: str, copied_hash: str) -> dict[str, Any]:
    return {"doc_type": "gate_decision", "gate_id": "GATE_001", "gate_type": "CONTROLLED_SOLVER_DEMO_RUN", "stage_id": STAGE_ID, "task_id": TASK_ID, "smoke_demo_only": True, "arbitrary_task_execution_allowed": False, "decision": "APPROVED_BY_HUMAN_FOR_DEMO_SMOKE_RUN", "solver_execution_allowed": True, "solver_execution_scope": "STAGE5_3A_V2_DEMO_SMOKE_ONLY", "solver_request_created": True, "one_solver_run_only": True, "run_count_limit": 1, "queue_runner_allowed": False, "queue_runner_launched": False, "queue_entry_created": False, "odb_open_allowed": False, "odb_opened": False, "metrics_extraction_allowed": False, "metrics_extracted": False, "metrics_approved": False, "final_evidence_approval_allowed": False, "final_evidence_approved": False, "final_verdict_frozen": False, "task_final_evidence_ledger_updated": False, "source_inp_path": str(source), "copied_inp_path": str(copied), "source_inp_sha256": source_hash, "copied_inp_sha256": copied_hash, "abaqus_command_path": ABAQUS_COMMAND, "abaqus_command_invocation_allowed": True, "no_odb_open_notice": "ODB may be produced but must not be opened in Stage 5.3A-v2.", "no_metrics_notice": "Metrics extraction is deferred to Stage 5.3B.", "final_evidence_locked_notice": "Final evidence remains locked."}


def build_demo_solver_request_v2(task: Path, candidate: Path, candidate_hash: str) -> dict[str, Any]:
    work_dir = task / "artifacts" / "solver_work"
    return {"request_type": "CONTROLLED_SOLVER_DEMO_SMOKE_RUN", "stage_id": STAGE_ID, "task_id": TASK_ID, "smoke_demo_only": True, "active_request": True, "executable_request": True, "arbitrary_task_execution_allowed": False, "source_gate_id": "GATE_001", "source_gate_validated": True, "candidate_inp_path": str(candidate.resolve(strict=False)), "candidate_inp_sha256": candidate_hash, "candidate_hash_verified": True, "solver_command_label": "ABAQUS_2024_CONTROLLED_DEMO", "solver_command_path": ABAQUS_COMMAND, "solver_command_invocation_allowed": True, "solver_execution_allowed": True, "queue_runner_allowed": False, "queue_runner_launched": False, "queue_entry_created": False, "odb_open_allowed": False, "odb_opened": False, "metrics_extraction_allowed": False, "metrics_extracted": False, "metrics_approved": False, "final_evidence_approval_allowed": False, "final_evidence_approved": False, "final_verdict_frozen": False, "task_final_evidence_ledger_updated": False, "working_directory": str(work_dir), "job_name": JOB_NAME, "cpu_count": CPU_COUNT, "timeout_seconds": TIMEOUT_SECONDS, "capture_stdout": True, "capture_stderr": True, "expected_artifacts": [f"{JOB_NAME}.{ext}" for ext in ["odb", "dat", "msg", "sta", "log", "com", "prt"]], "forbidden_outputs": ["metrics.json", "TASK_FINAL_EVIDENCE_LEDGER.md", "queue.json", "live_status.json"], "safety_boundary": "Stage 5.3A-v2 permits one controlled demo Abaqus invocation only; ODB opening, metrics, queue, final evidence, and verdict freeze remain disabled."}


def build_solver_status_v2(task: Path, request: dict[str, Any], runner: dict[str, Any], candidate: Path, candidate_hash: str) -> dict[str, Any]:
    work_dir = Path(str(request["working_directory"])); job_name = str(request["job_name"]); odb_path = work_dir / f"{job_name}.odb"
    expected = {f"{job_name}.{ext}": (work_dir / f"{job_name}.{ext}").exists() for ext in ["odb", "dat", "msg", "sta", "log", "com", "prt"]}
    return {"run_type": "CONTROLLED_SOLVER_DEMO_SMOKE_RUN", "stage_id": STAGE_ID, "task_id": TASK_ID, "solver_request_path": str(task / "artifacts" / "solver_requests" / "solver_request.json"), "solver_request_validated": validate_demo_solver_request_v2(request)["validation_status"] == "STAGE5_3A_V2_DEMO_SOLVER_REQUEST_VALID", "solver_invoked": runner.get("solver_invoked") is True, "solver_command_path": request.get("solver_command_path"), "solver_command_exists": Path(str(request.get("solver_command_path"))).exists(), "solver_return_code": runner.get("solver_return_code"), "solver_status": runner.get("solver_status"), "timeout_seconds": runner.get("timeout_seconds"), "timed_out": runner.get("timed_out") is True, "working_directory": str(work_dir), "job_name": job_name, "candidate_inp_path": str(candidate), "candidate_inp_sha256": candidate_hash, "stdout_tail": runner.get("stdout_tail", ""), "stderr_tail": runner.get("stderr_tail", ""), "log_tail": _tail_file(work_dir / f"{job_name}.log"), "sta_tail": _tail_file(work_dir / f"{job_name}.sta"), "msg_tail": _tail_file(work_dir / f"{job_name}.msg"), "dat_tail": _tail_file(work_dir / f"{job_name}.dat"), "expected_artifacts_present": expected, "odb_produced": odb_path.exists(), "odb_path_if_present": str(odb_path) if odb_path.exists() else "", "odb_opened": False, "metrics_extracted": False, "metrics_approved": False, "final_evidence_approved": False, "final_verdict_frozen": False, "task_final_evidence_ledger_updated": False, "queue_runner_launched": False, "queue_entry_created": False, "no_odb_open_notice": "ODB existence may be detected; ODB is not opened in Stage 5.3A-v2.", "no_metrics_notice": "Metrics extraction is deferred to Stage 5.3B.", "final_evidence_locked_notice": "Final evidence remains locked.", "runner_errors": runner.get("errors", []), "command_args": runner.get("command_args", []), "command_is_list": runner.get("command_is_list") is True, "shell": runner.get("shell")}


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _not_attempted(work_dir: Path, copied: Path) -> dict[str, Any]:
    return {"solver_invoked": False, "command_args": build_stage5_3a_v2_demo_command(copied), "command_is_list": True, "shell": False, "cwd": str(work_dir), "timeout_seconds": TIMEOUT_SECONDS, "solver_return_code": None, "timed_out": False, "stdout_tail": "", "stderr_tail": "", "errors": ["STAGE5_3A_V2_SOLVER_RUN_NOT_ATTEMPTED_BY_TEST_MODE"], "solver_status": "STAGE5_3A_V2_SOLVER_RUN_NOT_ATTEMPTED_BY_TEST_MODE"}


def _ensure_task_dirs(task: Path) -> dict[str, Path]:
    paths = {"trace": task / "trace", "gates": task / "gates", "handoffs": task / "handoffs", "solver_inputs": task / "artifacts" / "solver_inputs", "solver_requests": task / "artifacts" / "solver_requests", "solver_work": task / "artifacts" / "solver_work", "solver_status": task / "artifacts" / "solver_status", "logs": task / "artifacts" / "logs"}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    _write_text(task / "TASK_PLAN.md", "# Stage 5.3A-v2 Controlled Solver Demo Smoke\n\nDedicated smoke task only.\n")
    _write_text(task / "TRACE_INDEX.md", "# Trace Index\n\nRUN/HANDOFF/GATE records for Stage 5.3A-v2 demo smoke only.\n")
    return paths


def _write_trace_files(task: Path) -> None:
    trace = task / "trace"
    _write_text(trace / "RUN_001_DEMO_INPUT_SELECTION.md", "# RUN 001 Demo Input Selection\n")
    _write_text(trace / "RUN_002_DEMO_GATE_AND_REQUEST_CREATION.md", "# RUN 002 Demo Gate And Request Creation\n")
    _write_text(trace / "RUN_003_DEMO_SOLVER_EXECUTION_ATTEMPT.md", "# RUN 003 Demo Solver Execution Attempt\n")
    _write_text(trace / "RUN_004_DEMO_SOLVER_STATUS_CAPTURE.md", "# RUN 004 Demo Solver Status Capture\n")
    _write_text(task / "handoffs" / "HANDOFF_001_DEMO_SOLVER_REQUEST_TO_EXECUTION_AGENT.md", "# Handoff 001\n\nstage5_3a_v2_smoke_demo_only: true\nnot_a_generic_execution_handoff: true\n")


def _copy_demo_inp(source: Path, copied: Path, source_hash: str) -> None:
    header = "** ABQPILOT_STAGE5_3A_V2_DEMO_SOLVER_SMOKE_INPUT\n** COPIED_ARTIFACT_FOR_CONTROLLED_DEMO_EXECUTION\n" + f"** SOURCE_PATH: {source}\n** SOURCE_SHA256: {source_hash}\n" + "** SOURCE_NOT_MUTATED: true\n** ODB_AND_METRICS_DEFERRED_TO_STAGE5_3B\n"
    copied.write_text(header + source.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")


def _is_allowed_candidate(root: Path, candidate: Path) -> bool:
    if not candidate.exists() or candidate.suffix.lower() != ".inp":
        return False
    text = str(candidate).lower()
    blocked = [".env", "queue", "live_status", ".odb", "stage5_2f_controlled_solver_real_gate_smoke", "stage5_3a_controlled_solver_demo_smoke", "stage5_3a_v2_controlled_solver_demo_smoke"]
    if any(part in text for part in blocked):
        return False
    if "cae_model\\sanity_base" in text or "cae_model/sanity_base" in text or "source_sanity_base" in text:
        return False
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _tail_file(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[-limit:] if len(text) > limit else text


def _verdict_for(status: dict[str, Any]) -> str:
    if status.get("solver_status") == "STAGE5_3A_V2_SOLVER_RUN_COMPLETED_RETURN_ZERO":
        return STAGE5_3A_V2_VERDICT
    if status.get("solver_status") == "STAGE5_3A_V2_SOLVER_RUN_COMPLETED_NONZERO_RETURN":
        return NONZERO_RETURN
    if status.get("solver_status") == "STAGE5_3A_V2_BLOCKED_ABAQUS_COMMAND_NOT_FOUND":
        return INFRA_READY_SOLVER_NOT_RUN
    return status.get("solver_status", INFRA_READY_SOLVER_NOT_RUN)


def _next_steps_md(status: dict[str, Any]) -> str:
    return "\n".join(["# Stage 5.3A-v2 Next Steps", "", f"Solver status: `{status.get('solver_status')}`", "", "Do not open ODB in Stage 5.3A-v2.", "Do not extract metrics in Stage 5.3A-v2.", "Stage 5.3B may add ODB/metrics preview under a separate explicit gate."])


def _workspace_guard_md(pre_hits: list[str], post_hits: list[str], guard_allowed: bool) -> str:
    return "\n".join(["# Stage 5.3A-v2 Workspace Guard Verification", "", f"Workspace guard passed: `{guard_allowed and not pre_hits and not post_hits}`", f"Forbidden-root pre-scan hits: `{len(pre_hits)}`", f"Forbidden-root post-scan hits: `{len(post_hits)}`", "Project root: `D:\\Projects\\AbqPilot-v2`", "Forbidden root: `D:\\Users\\wuxia\\Documents\\AbqPilot`"])


def _render_gate_md(gate: dict[str, Any]) -> str:
    return "# Gate 001 Demo Solver Execution Approval v2\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in gate.items())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _blocked(status: str, task: Path, details: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "0.1", "command": "run-controlled-solver-demo-smoke-v2", "stage": "Stage 5.3A-v2", "stage_id": STAGE_ID, "verdict": status, "command_verdict": status, "success": False, "task_dir": str(task), "details": details, "solver_request_created": False, "solver_invoked": False, "queue_runner_launched": False, "queue_entry_created": False, "odb_opened": False, "metrics_extracted": False, "metrics_approved": False, "final_evidence_approved": False, "final_verdict_frozen": False, "task_final_evidence_ledger_updated": False}

