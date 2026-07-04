from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.acom.non_solver_revalidation_schema import HIGH_RISK_BLOCKED_AGENTS, SUPPORTED_NON_SOLVER_AGENTS
from abqpilot.acom.supervisor_non_solver_ledger import append_non_solver_ledger_entry
from abqpilot.acom.supervisor_non_solver_report import (
    handoff_rel,
    render_gate_record,
    render_handoff_record,
    render_run_record,
    render_summary_report,
    render_supervisor_review_report,
)
from abqpilot.acom.supervisor_non_solver_review_schema import (
    ACCEPTED_STATUS,
    ACCEPTED_WARNINGS_STATUS,
    SCHEMA_VERSION,
    STAGE,
    validate_supervisor_non_solver_review,
)
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_report import generate_protocol_report
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


PASS_INPUT = "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR"
WARNING_INPUT = "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR"


def supervisor_review_non_solver_revalidation(
    task_dir: str | Path,
    revalidation_result: str | Path | None = None,
    review_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    result_path, source = _find_source_result(task, revalidation_result)
    if not source:
        return _blocked_command(task, "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_MISSING_RESULT", ["missing REVALIDATION_EXECUTION_RESULT.json"])
    review = _build_review(task, result_path, source, review_id)
    review_dir = task / "supervisor_review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review["review_result_path"] = str(review_dir / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json")
    review["review_report_path"] = str(review_dir / "SUPERVISOR_NON_SOLVER_REVIEW_REPORT.md")
    if review["review_status"] in {ACCEPTED_STATUS, ACCEPTED_WARNINGS_STATUS}:
        _assign_pipeline_records(task, review, accepted=True)
        ledger = append_non_solver_ledger_entry(task, review)
        review["non_solver_ledger_entry_created"] = True
        review["ledger_md_path"] = ledger["ledger_md"]
        review["ledger_json_path"] = ledger["ledger_json"]
    else:
        _assign_pipeline_records(task, review, accepted=False)
    valid, errors = validate_supervisor_non_solver_review(review)
    if not valid:
        review["review_status"] = "SUPERVISOR_NON_SOLVER_REVIEW_REQUIRES_HUMAN_REVIEW"
        review["fail_items"].extend(errors)
        review["gate_decision"] = "BLOCKED"
        review["non_solver_ledger_entry_created"] = False
    Path(review["review_result_path"]).write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(review["review_report_path"]).write_text(render_supervisor_review_report(review), encoding="utf-8")
    Path(review["run_record_path"]).write_text(render_run_record(review), encoding="utf-8")
    Path(review["gate_path"]).write_text(render_gate_record(review), encoding="utf-8")
    if review.get("handoff_path"):
        Path(review["handoff_path"]).write_text(render_handoff_record(review), encoding="utf-8")
    protocol = validate_task_protocol(task)
    review["protocol_validation"] = protocol.get("verdict")
    if not protocol["success"] and review["review_status"] in {ACCEPTED_STATUS, ACCEPTED_WARNINGS_STATUS}:
        review["review_status"] = "SUPERVISOR_NON_SOLVER_REVIEW_REQUIRES_HUMAN_REVIEW"
        review["fail_items"].extend(protocol.get("errors", []))
        review["gate_decision"] = "BLOCKED"
    Path(review["review_result_path"]).write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(review["review_report_path"]).write_text(render_supervisor_review_report(review), encoding="utf-8")
    return _command_result(task, review, success=review["review_status"] in {ACCEPTED_STATUS, ACCEPTED_WARNINGS_STATUS})


def report_supervisor_non_solver_review(
    task_dir: str | Path,
    revalidation_result: str | Path | None = None,
    review_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    review_path = task / "supervisor_review" / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json"
    if not review_path.exists():
        return {
            "command": "report-supervisor-non-solver-review",
            "verdict": "SUPERVISOR_NON_SOLVER_REVIEW_REPORT_MISSING",
            "success": False,
            "errors": ["missing supervisor review result"],
            "warnings": [],
            "details": {"task_dir": str(task)},
        }
    review = json.loads(review_path.read_text(encoding="utf-8"))
    report_path = task / "SUPERVISOR_NON_SOLVER_REVIEW_SUMMARY.md"
    protocol = generate_protocol_report(task)
    report_path.write_text(render_summary_report(review) + f"\n## Pipeline Protocol\n`{protocol.get('validation_verdict')}`\n", encoding="utf-8")
    return {
        "command": "report-supervisor-non-solver-review",
        "verdict": "SUPERVISOR_NON_SOLVER_REVIEW_REPORT_READY",
        "success": True,
        "errors": [],
        "warnings": [],
        "output_paths": {"report_path": str(report_path), "review_result": str(review_path)},
        "details": review | {"protocol_validation": protocol.get("validation_verdict")},
    }


def _build_review(task: Path, source_path: Path, source: dict[str, Any], review_id: str | None) -> dict[str, Any]:
    agent = source.get("downstream_agent")
    reviewed_status = source.get("result_status")
    checks: list[dict[str, str]] = []
    pass_items: list[str] = []
    warning_items: list[str] = []
    fail_items: list[str] = []

    def add(name: str, ok: bool, detail: str, *, warning: bool = False) -> None:
        status = "pass" if ok else ("warning" if warning else "fail")
        checks.append({"name": name, "status": status, "detail": detail})
        target = pass_items if status == "pass" else warning_items if status == "warning" else fail_items
        target.append(f"{name}: {detail}")

    add("reviewed agent supported for Stage 5.0F", agent in SUPPORTED_NON_SOLVER_AGENTS, str(agent))
    add("reviewed agent is not high risk", agent not in HIGH_RISK_BLOCKED_AGENTS, str(agent))
    add("reviewed status is supervisor-pending", reviewed_status in {PASS_INPUT, WARNING_INPUT}, str(reviewed_status))
    add("final_evidence_approved is false", source.get("final_evidence_approved") is False, str(source.get("final_evidence_approved")))
    add("automatic_execution_performed is false", source.get("automatic_execution_performed") is False, str(source.get("automatic_execution_performed")))
    unsafe_flags = _unsafe_flags(source)
    add("unsafe flags are false", not unsafe_flags, ", ".join(unsafe_flags) if unsafe_flags else "all false")
    approval_attempts = _approval_attempts(source)
    add("no final/solver/ODB approval attempt", not approval_attempts, ", ".join(approval_attempts) if approval_attempts else "none")
    records_ok, record_detail = _records_exist_and_gate_is_pending(source)
    add("Stage 5.0F RUN/GATE/HANDOFF records exist and gate is pending supervisor review", records_ok, record_detail)

    if agent in HIGH_RISK_BLOCKED_AGENTS:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_HIGH_RISK_AGENT"
    elif agent not in SUPPORTED_NON_SOLVER_AGENTS:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSUPPORTED_AGENT"
    elif approval_attempts:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"
    elif source.get("automatic_execution_performed") is not False:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_AUTOMATIC_EXECUTION"
    elif unsafe_flags:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSAFE_FLAGS"
    elif not records_ok:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_MISSING_RECORDS"
    elif reviewed_status == PASS_INPUT:
        review_status = ACCEPTED_STATUS
    elif reviewed_status == WARNING_INPUT:
        review_status = ACCEPTED_WARNINGS_STATUS
    else:
        review_status = "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FAILED_REVALIDATION"

    gate_decision = _gate_decision_for_status(review_status)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": source.get("task_id") or task.name,
        "task_dir": str(task),
        "review_id": review_id or "latest",
        "source_revalidation_result_path": str(source_path),
        "source_revalidation_report_path": source.get("report_path"),
        "reviewed_agent": agent,
        "reviewed_status": reviewed_status,
        "review_status": review_status,
        "gate_decision": gate_decision,
        "checks": checks,
        "pass_items": pass_items,
        "warning_items": warning_items,
        "fail_items": fail_items,
        "artifacts_reviewed": [str(source_path), str(source.get("report_path")), str(source.get("run_record_path")), str(source.get("gate_path")), str(source.get("handoff_path"))],
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "non_solver_ledger_entry_created": False,
        "codex_summary_is_final_evidence": False,
        "next_action": "EvidenceReportAgent may summarize the non-solver ledger." if gate_decision != "BLOCKED" else "Blocked; do not advance to evidence summary.",
        "safety_flags": _safe_flags(),
    }


def _find_source_result(task: Path, explicit: str | Path | None) -> tuple[Path | None, dict[str, Any] | None]:
    if explicit:
        path = Path(explicit)
        return (path, json.loads(path.read_text(encoding="utf-8"))) if path.exists() else (None, None)
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    for path in (task / "revalidation").glob("*_*/REVALIDATION_EXECUTION_RESULT.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates.append((path.stat().st_mtime, path, payload))
    if not candidates:
        return None, None
    _mtime, path, payload = sorted(candidates, reverse=True)[0]
    return path, payload


def _assign_pipeline_records(task: Path, review: dict[str, Any], *, accepted: bool) -> None:
    for child in ("trace", "handoffs", "gates"):
        (task / child).mkdir(parents=True, exist_ok=True)
    run_id = _next_available_id(task / "trace", "RUN", 18)
    gate_id = _next_available_id(task / "gates", "GATE", 14)
    handoff_id = _next_available_id(task / "handoffs", "HANDOFF", 17)
    run_path = task / "trace" / f"{run_id}_PIPELINE_SUPERVISOR_NON_SOLVER_REVIEW.md"
    gate_path = task / "gates" / f"{gate_id}_SUPERVISOR_NON_SOLVER_REVIEW.md"
    handoff_path = task / "handoffs" / f"{handoff_id}_SUPERVISOR_NON_SOLVER_REVIEW_TO_EVIDENCE_REPORT_AGENT.md"
    source_handoff = _handoff_in_from_source(review)
    review.update(
        {
            "run_id": run_id,
            "gate_id": gate_id,
            "handoff_id": handoff_id if accepted else None,
            "run_record_path": str(run_path),
            "gate_path": str(gate_path),
            "handoff_path": str(handoff_path) if accepted else None,
            "handoff_in_rel": source_handoff,
            "handoff_out_rel": f"handoffs/{handoff_path.name}" if accepted else "none",
        }
    )


def _handoff_in_from_source(review: dict[str, Any]) -> str:
    try:
        source = json.loads(Path(review["source_revalidation_result_path"]).read_text(encoding="utf-8"))
    except Exception:
        return "none"
    return handoff_rel(source.get("handoff_path"))


def _records_exist_and_gate_is_pending(source: dict[str, Any]) -> tuple[bool, str]:
    missing = [key for key in ["run_record_path", "gate_path", "handoff_path"] if not source.get(key) or not Path(source[key]).exists()]
    if missing:
        return False, f"missing records: {', '.join(missing)}"
    gate = load_frontmatter(source["gate_path"])
    decision = gate.get("decision")
    if decision == "APPROVED":
        return False, "Stage 5.0F gate must not be APPROVED"
    if decision != "PENDING_SUPERVISOR_REVIEW":
        return False, f"Stage 5.0F gate decision is {decision}"
    return True, "records present and gate is PENDING_SUPERVISOR_REVIEW"


def _unsafe_flags(source: dict[str, Any]) -> list[str]:
    flags = source.get("safety_flags") or {}
    return [key for key, value in flags.items() if value is True]


def _approval_attempts(source: dict[str, Any]) -> list[str]:
    keys = ["final_evidence_approved", "final_verdict_frozen", "solver_approved", "odb_metrics_approved"]
    attempts = [key for key in keys if source.get(key) is True]
    flags = source.get("safety_flags") or {}
    attempts.extend(key for key in keys if flags.get(key) is True)
    return attempts


def _gate_decision_for_status(status: str) -> str:
    if status == ACCEPTED_STATUS:
        return "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER"
    if status == ACCEPTED_WARNINGS_STATUS:
        return "ACCEPTED_WITH_WARNINGS_FOR_NON_SOLVER_EVIDENCE_LEDGER"
    return "BLOCKED"


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


def _blocked_command(task: Path, status: str, errors: list[str]) -> dict[str, Any]:
    return {
        "command": "supervisor-review-non-solver-revalidation",
        "verdict": status,
        "success": False,
        "errors": errors,
        "warnings": [],
        "output_paths": {},
        "details": {
            "task_dir": str(task),
            "review_status": status,
            "gate_decision": "BLOCKED",
            "final_evidence_approved": False,
            "final_verdict_frozen": False,
            "solver_approved": False,
            "odb_metrics_approved": False,
        },
    }


def _command_result(task: Path, review: dict[str, Any], success: bool) -> dict[str, Any]:
    return {
        "command": "supervisor-review-non-solver-revalidation",
        "verdict": review["review_status"],
        "success": success,
        "errors": review.get("fail_items", []) if not success else [],
        "warnings": review.get("warning_items", []),
        "output_paths": {
            "review_result": review.get("review_result_path"),
            "review_report": review.get("review_report_path"),
            "run_record": review.get("run_record_path"),
            "gate": review.get("gate_path"),
            "handoff": review.get("handoff_path"),
            "ledger_md": review.get("ledger_md_path"),
            "ledger_json": review.get("ledger_json_path"),
        },
        "details": review | {"task_dir": str(task)},
    }
