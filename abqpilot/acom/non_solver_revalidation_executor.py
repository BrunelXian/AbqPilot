from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.acom.non_solver_revalidation_profiles import run_profile_checks, summarize_checks
from abqpilot.acom.non_solver_revalidation_report import (
    render_execution_report,
    render_gate_record,
    render_handoff_record,
    render_run_record,
    render_summary_report,
)
from abqpilot.acom.non_solver_revalidation_schema import (
    FAIL_STATUS,
    HIGH_RISK_BLOCKED_AGENTS,
    PASS_STATUS,
    SCHEMA_VERSION,
    STAGE,
    SUPPORTED_NON_SOLVER_AGENTS,
    WARNING_STATUS,
    validate_non_solver_revalidation_result,
)
from abqpilot.pipeline_protocol.protocol_report import generate_protocol_report
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


ACCEPTED_STATUS = "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"


def execute_non_solver_revalidation(
    task_dir: str | Path,
    revalidation_dir: str | Path | None = None,
    agent: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    selected = _find_scaffold(task, revalidation_dir, agent)
    if selected is None:
        return _blocked_result(task, None, "NON_SOLVER_REVALIDATION_BLOCKED_MISSING_SCAFFOLD", ["missing revalidation scaffold"])
    scaffold_path, scaffold = selected
    package_dir = scaffold_path.parent
    downstream_agent = scaffold.get("downstream_agent")
    intake_path = Path(scaffold.get("acom_intake_path") or task / "codex_result" / "acom_result_intake.json")
    intake = _load_json_if_exists(intake_path)
    if scaffold.get("status") != "REVALIDATION_SCAFFOLD_READY":
        return _write_blocked_execution(task, package_dir, scaffold, "NON_SOLVER_REVALIDATION_BLOCKED_MISSING_SCAFFOLD", [f"scaffold status is {scaffold.get('status')}"])
    if intake.get("result_status") != ACCEPTED_STATUS:
        return _write_blocked_execution(
            task,
            package_dir,
            scaffold,
            "NON_SOLVER_REVALIDATION_BLOCKED_ACOM_INTAKE_NOT_ACCEPTED",
            [f"ACOM intake status is {intake.get('result_status')}"],
        )
    if downstream_agent in HIGH_RISK_BLOCKED_AGENTS:
        return _write_blocked_execution(
            task,
            package_dir,
            scaffold,
            "NON_SOLVER_REVALIDATION_BLOCKED_HIGH_RISK_AGENT",
            [f"{downstream_agent} is high-risk and unsupported in Stage 5.0F"],
        )
    if downstream_agent not in SUPPORTED_NON_SOLVER_AGENTS:
        return _write_blocked_execution(
            task,
            package_dir,
            scaffold,
            "NON_SOLVER_REVALIDATION_BLOCKED_UNSUPPORTED_AGENT",
            [f"{downstream_agent} is not supported in Stage 5.0F"],
        )
    structured_result_path = Path(scaffold.get("structured_result_path") or intake.get("result_json") or task / "codex_result" / "structured_result.json")
    structured_result = _load_json_if_exists(structured_result_path)
    checks = run_profile_checks(downstream_agent, task_dir=task, scaffold=scaffold, intake=intake, structured_result=structured_result)
    summary = summarize_checks(checks)
    if summary["fail_items"]:
        status = FAIL_STATUS
    elif summary["warning_items"]:
        status = WARNING_STATUS
    else:
        status = PASS_STATUS
    result = _base_execution_result(
        task=task,
        package_dir=package_dir,
        scaffold=scaffold,
        scaffold_path=scaffold_path,
        intake=intake,
        structured_result_path=structured_result_path,
        status=status,
        checks=checks,
        summary=summary,
    )
    _assign_pipeline_records(task, result)
    result_path = package_dir / "REVALIDATION_EXECUTION_RESULT.json"
    report_path = package_dir / "REVALIDATION_EXECUTION_REPORT.md"
    result["result_path"] = str(result_path)
    result["report_path"] = str(report_path)
    result["gate_decision"] = "PENDING_SUPERVISOR_REVIEW" if status != FAIL_STATUS else "BLOCKED"
    valid, errors = validate_non_solver_revalidation_result(result)
    if not valid:
        result["result_status"] = "NON_SOLVER_REVALIDATION_REVIEW_REQUIRED"
        result["fail_items"].extend(errors)
        result["gate_decision"] = "BLOCKED"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_execution_report(result), encoding="utf-8")
    Path(result["run_record_path"]).write_text(render_run_record(result), encoding="utf-8")
    Path(result["gate_path"]).write_text(render_gate_record(result), encoding="utf-8")
    Path(result["handoff_path"]).write_text(render_handoff_record(result), encoding="utf-8")
    protocol = validate_task_protocol(task)
    if not protocol["success"]:
        result["result_status"] = "NON_SOLVER_REVALIDATION_BLOCKED_PROTOCOL_INVALID"
        result["protocol_errors"] = protocol.get("errors", [])
        result["gate_decision"] = "BLOCKED"
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        report_path.write_text(render_execution_report(result), encoding="utf-8")
    result["protocol_validation"] = protocol.get("verdict")
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return _command_result(task, result, success=result["result_status"] not in {"NON_SOLVER_REVALIDATION_FAIL_BLOCKED", "NON_SOLVER_REVALIDATION_BLOCKED_PROTOCOL_INVALID"})


def report_non_solver_revalidation(
    task_dir: str | Path,
    revalidation_dir: str | Path | None = None,
    agent: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    result_path, payload = _find_execution_result(task, revalidation_dir, agent)
    if not payload:
        return {
            "command": "report-non-solver-revalidation",
            "verdict": "NON_SOLVER_REVALIDATION_REPORT_MISSING",
            "success": False,
            "errors": ["missing non-solver revalidation execution result"],
            "warnings": [],
            "details": {"task_dir": str(task)},
        }
    report_path = task / "NON_SOLVER_REVALIDATION_REPORT.md"
    protocol = generate_protocol_report(task)
    report_path.write_text(render_summary_report(payload) + f"\n## Pipeline Protocol\n`{protocol.get('validation_verdict')}`\n", encoding="utf-8")
    return {
        "command": "report-non-solver-revalidation",
        "verdict": "NON_SOLVER_REVALIDATION_REPORT_READY",
        "success": True,
        "errors": [],
        "warnings": [],
        "output_paths": {"report_path": str(report_path), "execution_result": str(result_path)},
        "details": payload | {"protocol_validation": protocol.get("validation_verdict")},
    }


def _base_execution_result(
    *,
    task: Path,
    package_dir: Path,
    scaffold: dict[str, Any],
    scaffold_path: Path,
    intake: dict[str, Any],
    structured_result_path: Path,
    status: str,
    checks: list[Any],
    summary: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": scaffold.get("task_id") or task.name,
        "task_dir": str(task),
        "revalidation_dir": str(package_dir),
        "scaffold_path": str(scaffold_path),
        "scaffold_status": scaffold.get("status"),
        "source_handoff_path": scaffold.get("source_handoff_path"),
        "handoff_in_rel": scaffold.get("handoff_in_rel"),
        "downstream_agent": scaffold.get("downstream_agent"),
        "acom_intake_path": scaffold.get("acom_intake_path"),
        "structured_result_path": str(structured_result_path),
        "intake_status": intake.get("result_status"),
        "result_status": status,
        "checks": [{"name": item.name, "status": item.status, "detail": item.detail} for item in checks],
        "pass_items": summary["pass_items"],
        "warning_items": summary["warning_items"],
        "fail_items": summary["fail_items"],
        "gate_decision": "PENDING_SUPERVISOR_REVIEW" if status != FAIL_STATUS else "BLOCKED",
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "codex_summary_is_final_evidence": False,
        "abqpilot_revalidation_required": True,
        "next_supervisor_action": "PipelineSupervisor reviews the non-solver revalidation result gate.",
        "safety_flags": _safe_flags(),
    }


def _write_blocked_execution(task: Path, package_dir: Path, scaffold: dict[str, Any], status: str, errors: list[str]) -> dict[str, Any]:
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": scaffold.get("task_id") or task.name,
        "task_dir": str(task),
        "revalidation_dir": str(package_dir),
        "scaffold_path": str(package_dir / "REVALIDATION_SCAFFOLD.json"),
        "scaffold_status": scaffold.get("status"),
        "downstream_agent": scaffold.get("downstream_agent"),
        "acom_intake_path": scaffold.get("acom_intake_path"),
        "structured_result_path": scaffold.get("structured_result_path"),
        "intake_status": None,
        "result_status": status,
        "checks": [],
        "pass_items": [],
        "warning_items": [],
        "fail_items": errors,
        "gate_decision": "BLOCKED",
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "codex_summary_is_final_evidence": False,
        "abqpilot_revalidation_required": True,
        "next_supervisor_action": "No pipeline advance. Select a later guarded stage for this downstream agent.",
        "safety_flags": _safe_flags(),
    }
    result_path = package_dir / "REVALIDATION_EXECUTION_RESULT.json"
    report_path = package_dir / "REVALIDATION_EXECUTION_REPORT.md"
    result["result_path"] = str(result_path)
    result["report_path"] = str(report_path)
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_execution_report(result), encoding="utf-8")
    return _command_result(task, result, success=False)


def _blocked_result(task: Path, package_dir: Path | None, status: str, errors: list[str]) -> dict[str, Any]:
    return {
        "command": "execute-non-solver-revalidation",
        "verdict": status,
        "success": False,
        "errors": errors,
        "warnings": [],
        "output_paths": {},
        "details": {
            "task_dir": str(task),
            "revalidation_dir": str(package_dir) if package_dir else None,
            "result_status": status,
            "gate_decision": "BLOCKED",
            "automatic_execution_performed": False,
            "final_evidence_approved": False,
        },
    }


def _command_result(task: Path, result: dict[str, Any], success: bool) -> dict[str, Any]:
    return {
        "command": "execute-non-solver-revalidation",
        "verdict": result["result_status"],
        "success": success,
        "errors": result.get("fail_items", []) if not success else [],
        "warnings": result.get("warning_items", []),
        "output_paths": {
            "execution_result": result.get("result_path"),
            "execution_report": result.get("report_path"),
            "run_record": result.get("run_record_path"),
            "gate": result.get("gate_path"),
            "handoff": result.get("handoff_path"),
        },
        "details": result | {"task_dir": str(task)},
    }


def _assign_pipeline_records(task: Path, result: dict[str, Any]) -> None:
    for child in ("trace", "handoffs", "gates"):
        (task / child).mkdir(parents=True, exist_ok=True)
    run_id = _next_available_id(task / "trace", "RUN", 16)
    gate_id = _next_available_id(task / "gates", "GATE", 12)
    handoff_id = _next_available_id(task / "handoffs", "HANDOFF", 15)
    token = _agent_token(result["downstream_agent"])
    run_path = task / "trace" / f"{run_id}_{token}_REVALIDATION_RESULT.md"
    gate_path = task / "gates" / f"{gate_id}_{token}_REVALIDATION_RESULT.md"
    handoff_path = task / "handoffs" / f"{handoff_id}_{token}_REVALIDATION_RESULT_TO_PIPELINE_SUPERVISOR.md"
    result.update(
        {
            "run_id": run_id,
            "gate_id": gate_id,
            "handoff_id": handoff_id,
            "run_record_path": str(run_path),
            "gate_path": str(gate_path),
            "handoff_path": str(handoff_path),
            "handoff_in_rel": result.get("handoff_in_rel") or _relative_handoff(result.get("source_handoff_path")),
            "handoff_out_rel": f"handoffs/{handoff_path.name}",
        }
    )


def _relative_handoff(path_value: str | None) -> str:
    if not path_value:
        return "none"
    path = Path(path_value)
    return f"handoffs/{path.name}"


def _find_scaffold(task: Path, revalidation_dir: str | Path | None, agent: str | None) -> tuple[Path, dict[str, Any]] | None:
    if revalidation_dir:
        path = Path(revalidation_dir) / "REVALIDATION_SCAFFOLD.json"
        if path.exists():
            return path, json.loads(path.read_text(encoding="utf-8"))
        return None
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    for path in (task / "revalidation").glob("*_*/REVALIDATION_SCAFFOLD.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if agent and payload.get("downstream_agent") != agent:
            continue
        candidates.append((path.stat().st_mtime, path, payload))
    if not candidates:
        return None
    _mtime, path, payload = sorted(candidates, reverse=True)[0]
    return path, payload


def _find_execution_result(task: Path, revalidation_dir: str | Path | None, agent: str | None) -> tuple[Path | None, dict[str, Any] | None]:
    if revalidation_dir:
        path = Path(revalidation_dir) / "REVALIDATION_EXECUTION_RESULT.json"
        return (path, json.loads(path.read_text(encoding="utf-8"))) if path.exists() else (None, None)
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    for path in (task / "revalidation").glob("*_*/REVALIDATION_EXECUTION_RESULT.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if agent and payload.get("downstream_agent") != agent:
            continue
        candidates.append((path.stat().st_mtime, path, payload))
    if not candidates:
        return None, None
    _mtime, path, payload = sorted(candidates, reverse=True)[0]
    return path, payload


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_flags() -> dict[str, bool]:
    return {
        "codex_cli_called": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "source_cae_mutated": False,
        "source_inp_mutated": False,
        "env_read": False,
        "shell_true_used": False,
        "automatic_scheduling_added": False,
        "high_risk_agent_executed": False,
    }


def _next_available_id(directory: Path, prefix: str, start: int) -> str:
    number = start
    while any(directory.glob(f"{prefix}_{number:03d}_*.md")):
        number += 1
    return f"{prefix}_{number:03d}"


def _agent_token(agent: str) -> str:
    token = agent
    append_agent = token.endswith("Agent")
    if append_agent:
        token = token[: -len("Agent")]
    chars: list[str] = []
    for index, ch in enumerate(token):
        if index and ch.isupper() and not token[index - 1].isupper():
            chars.append("_")
        chars.append(ch.upper())
    normalized = "".join(chars).replace("Q_A", "QA").replace("O_D_B", "ODB")
    return normalized + "_AGENT" if append_agent else normalized
