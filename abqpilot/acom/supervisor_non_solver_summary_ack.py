from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from abqpilot.acom.non_solver_evidence_summary_schema import (
    READY_GATE,
    READY_STATUS,
    READY_WARNINGS_GATE,
    READY_WARNINGS_STATUS,
    validate_non_solver_evidence_summary,
    validate_non_solver_ledger,
)
from abqpilot.acom.supervisor_non_solver_summary_ack_ledger import append_non_solver_summary_ack_ledger_entry
from abqpilot.acom.supervisor_non_solver_summary_ack_report import (
    rel_handoff,
    render_cli_ack_report,
    render_gate_record,
    render_handoff_record,
    render_run_record,
    render_supervisor_summary_ack_report,
)
from abqpilot.acom.supervisor_non_solver_summary_ack_schema import (
    ACK_ACCEPTED,
    ACK_ACCEPTED_WARNINGS,
    ACK_GATE,
    ACK_WARNINGS_GATE,
    SCHEMA_VERSION,
    STAGE,
    validate_supervisor_non_solver_summary_ack,
)
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_report import generate_protocol_report
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


def supervisor_ack_non_solver_summary(
    task_dir: str | Path,
    summary_result: str | Path | None = None,
    ack_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    final_ledger = task / "TASK_FINAL_EVIDENCE_LEDGER.md"
    before_hash = _sha256_or_none(final_ledger)
    ack = _build_ack(task, summary_result, ack_id, before_hash)
    _assign_pipeline_records(task, ack, accepted=ack["gate_decision"] != "BLOCKED")
    _write_ack_artifacts(ack)
    protocol = validate_task_protocol(task)
    ack["protocol_validation"] = protocol.get("verdict")
    if not protocol.get("success") and ack["gate_decision"] != "BLOCKED":
        ack["ack_status"] = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REVIEW_REQUIRED"
        ack["gate_decision"] = "BLOCKED"
        ack["fail_items"].extend(protocol.get("errors", []))
        ack["handoff_id"] = None
        ack["handoff_path"] = None
        ack["handoff_out_rel"] = "none"
    after_protocol_hash = _sha256_or_none(final_ledger)
    if before_hash != after_protocol_hash:
        ack["ack_status"] = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION"
        ack["gate_decision"] = "BLOCKED"
        ack["fail_items"].append("TASK_FINAL_EVIDENCE_LEDGER.md hash changed during acknowledgement record generation")
        ack["handoff_id"] = None
        ack["handoff_path"] = None
        ack["handoff_out_rel"] = "none"
    if ack["ack_status"] in {ACK_ACCEPTED, ACK_ACCEPTED_WARNINGS} and ack["gate_decision"] != "BLOCKED":
        ledger = append_non_solver_summary_ack_ledger_entry(task, ack)
        ack["non_solver_summary_ack_ledger_entry_created"] = True
        ack["ack_ledger_md_path"] = ledger["ledger_md"]
        ack["ack_ledger_json_path"] = ledger["ledger_json"]
    after_hash = _sha256_or_none(final_ledger)
    ack["task_final_evidence_ledger_hash_after"] = after_hash
    if before_hash != after_hash:
        ack["ack_status"] = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION"
        ack["gate_decision"] = "BLOCKED"
        ack["non_solver_summary_ack_ledger_entry_created"] = False
        ack["fail_items"].append("TASK_FINAL_EVIDENCE_LEDGER.md hash changed during acknowledgement")
    valid, schema_errors = validate_supervisor_non_solver_summary_ack(ack)
    if not valid and ack["gate_decision"] != "BLOCKED":
        ack["ack_status"] = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REVIEW_REQUIRED"
        ack["gate_decision"] = "BLOCKED"
        ack["non_solver_summary_ack_ledger_entry_created"] = False
        ack["fail_items"].extend(schema_errors)
        ack["handoff_id"] = None
        ack["handoff_path"] = None
        ack["handoff_out_rel"] = "none"
    _write_ack_artifacts(ack)
    return _command_result(task, ack, success=ack["ack_status"] in {ACK_ACCEPTED, ACK_ACCEPTED_WARNINGS})


def report_supervisor_non_solver_summary_ack(
    task_dir: str | Path,
    summary_result: str | Path | None = None,
    ack_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    ack_path = task / "supervisor_summary_ack" / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_RESULT.json"
    if not ack_path.exists():
        return {
            "command": "report-supervisor-non-solver-summary-ack",
            "verdict": "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REPORT_MISSING",
            "success": False,
            "errors": ["missing supervisor non-solver summary acknowledgement result"],
            "warnings": [],
            "output_paths": {},
            "details": {"task_dir": str(task)},
        }
    ack = json.loads(ack_path.read_text(encoding="utf-8"))
    report_path = task / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_SUMMARY.md"
    protocol = generate_protocol_report(task)
    report_path.write_text(
        render_cli_ack_report(ack) + f"\n## Pipeline Protocol\n`{protocol.get('validation_verdict')}`\n",
        encoding="utf-8",
    )
    return {
        "command": "report-supervisor-non-solver-summary-ack",
        "verdict": "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REPORT_READY",
        "success": True,
        "errors": [],
        "warnings": ack.get("warning_items", []),
        "output_paths": {"report_path": str(report_path), "ack_result": str(ack_path)},
        "details": ack | {"protocol_validation": protocol.get("validation_verdict")},
    }


def _build_ack(task: Path, explicit_summary: str | Path | None, ack_id: str | None, before_hash: str | None) -> dict[str, Any]:
    summary_path = Path(explicit_summary) if explicit_summary else task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"
    summary_report = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md"
    ledger_json = task / "NON_SOLVER_EVIDENCE_LEDGER.json"
    ledger_md = task / "NON_SOLVER_EVIDENCE_LEDGER.md"
    checks: list[dict[str, str]] = []
    pass_items: list[str] = []
    warning_items: list[str] = []
    fail_items: list[str] = []
    summary: dict[str, Any] = {}
    ledger_payload: dict[str, Any] = {}

    def check(name: str, ok: bool, detail: str, *, warning: bool = False) -> None:
        state = "pass" if ok else ("warning" if warning else "fail")
        checks.append({"name": name, "status": state, "detail": detail})
        target = pass_items if state == "pass" else warning_items if state == "warning" else fail_items
        target.append(f"{name}: {detail}")

    if not summary_path.exists() or not summary_report.exists():
        ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_SUMMARY"
        gate_decision = "BLOCKED"
        check("summary artifacts exist", False, f"missing {summary_path if not summary_path.exists() else summary_report}")
    else:
        check("summary artifacts exist", True, "summary result/report found")
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_INVALID_SUMMARY"
            gate_decision = "BLOCKED"
            check("summary JSON parses", False, str(exc))
        else:
            valid_summary, summary_errors = validate_non_solver_evidence_summary(summary)
            if summary.get("summary_status") not in {READY_STATUS, READY_WARNINGS_STATUS}:
                ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SUMMARY_NOT_READY"
                gate_decision = "BLOCKED"
            elif summary.get("gate_decision") not in {READY_GATE, READY_WARNINGS_GATE}:
                ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_INVALID_SUMMARY"
                gate_decision = "BLOCKED"
            elif not valid_summary:
                ack_status = _blocked_status_for_summary_errors(summary_errors)
                gate_decision = "BLOCKED"
            elif summary.get("summary_status") == READY_WARNINGS_STATUS:
                ack_status = ACK_ACCEPTED_WARNINGS
                gate_decision = ACK_WARNINGS_GATE
            else:
                ack_status = ACK_ACCEPTED
                gate_decision = ACK_GATE
            check("summary schema and status ready", valid_summary and summary.get("summary_status") in {READY_STATUS, READY_WARNINGS_STATUS}, "; ".join(summary_errors) if summary_errors else str(summary.get("summary_status")))
            if summary.get("summary_status") == READY_WARNINGS_STATUS:
                check("summary contains warnings", True, "acknowledged with warnings", warning=True)
    if not ledger_json.exists() or not ledger_md.exists():
        if locals().get("gate_decision") != "BLOCKED":
            ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_LEDGER"
            gate_decision = "BLOCKED"
        check("source non-solver ledger exists", False, f"missing {ledger_json if not ledger_json.exists() else ledger_md}")
    else:
        check("source non-solver ledger exists", True, "ledger found")
        try:
            ledger_payload = json.loads(ledger_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_LEDGER_INVALID"
            gate_decision = "BLOCKED"
            check("source non-solver ledger parses", False, str(exc))
        else:
            ledger_valid, ledger_errors, ledger_warnings = validate_non_solver_ledger(ledger_payload)
            if not ledger_valid and locals().get("gate_decision") != "BLOCKED":
                ack_status = _blocked_status_for_ledger_errors(ledger_errors)
                gate_decision = "BLOCKED"
            check("source non-solver ledger valid", ledger_valid, "; ".join(ledger_errors) if ledger_errors else "valid")
            for item in ledger_warnings:
                check("source ledger warning", True, item, warning=True)
    approval_attempts = _approval_attempts(summary, ledger_payload, task)
    if approval_attempts:
        ack_status = _blocked_status_for_approval_attempts(approval_attempts)
        gate_decision = "BLOCKED"
        check("no final/solver/ODB/final-ledger approval attempt", False, "; ".join(approval_attempts))
    elif summary:
        check("no final/solver/ODB/final-ledger approval attempt", True, "all checked flags are false")
    if before_hash != _sha256_or_none(task / "TASK_FINAL_EVIDENCE_LEDGER.md"):
        ack_status = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION"
        gate_decision = "BLOCKED"
        check("TASK_FINAL_EVIDENCE_LEDGER.md hash unchanged before acknowledgement", False, "hash changed before ack")
    else:
        check("TASK_FINAL_EVIDENCE_LEDGER.md hash unchanged before acknowledgement", True, str(before_hash))
    ack_status = locals().get("ack_status", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_SUMMARY")
    gate_decision = locals().get("gate_decision", "BLOCKED")
    entries = ledger_payload.get("entries", []) if isinstance(ledger_payload.get("entries"), list) else []
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": summary.get("task_id") or task.name,
        "task_dir": str(task),
        "ack_id": ack_id or "latest",
        "summary_result_path": str(summary_path),
        "summary_report_path": str(summary_report),
        "ledger_json_path": str(ledger_json),
        "ledger_md_path": str(ledger_md),
        "reviewed_summary_status": summary.get("summary_status"),
        "reviewed_gate_decision": summary.get("gate_decision"),
        "reviewed_entries_count": len(entries),
        "ack_status": ack_status,
        "gate_decision": gate_decision,
        "checks": checks,
        "pass_items": pass_items,
        "warning_items": warning_items,
        "fail_items": fail_items,
        "artifacts_reviewed": [str(path) for path in [summary_path, summary_report, ledger_json, ledger_md] if path.exists()],
        "task_final_evidence_ledger_hash_before": before_hash,
        "task_final_evidence_ledger_hash_after": before_hash,
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "task_final_evidence_ledger_updated": False,
        "non_solver_summary_ack_ledger_entry_created": False,
        "codex_summary_is_final_evidence": False,
        "next_action": "DocsStatusAgent may synchronize non-final project status documentation." if gate_decision != "BLOCKED" else "Blocked; do not advance.",
        "safety_flags": _safe_flags(),
    }


def _assign_pipeline_records(task: Path, ack: dict[str, Any], *, accepted: bool) -> None:
    ack_dir = task / "supervisor_summary_ack"
    ack_dir.mkdir(parents=True, exist_ok=True)
    for child in ("trace", "handoffs", "gates"):
        (task / child).mkdir(parents=True, exist_ok=True)
    run_id = _next_available_id(task / "trace", "RUN", 20)
    gate_id = _next_available_id(task / "gates", "GATE", 16)
    handoff_id = _next_available_id(task / "handoffs", "HANDOFF", 19)
    run_path = task / "trace" / f"{run_id}_PIPELINE_SUPERVISOR_NON_SOLVER_SUMMARY_ACK.md"
    gate_path = task / "gates" / f"{gate_id}_SUPERVISOR_NON_SOLVER_SUMMARY_ACK.md"
    handoff_path = task / "handoffs" / f"{handoff_id}_SUPERVISOR_NON_SOLVER_SUMMARY_ACK_TO_DOCS_STATUS_AGENT.md"
    ack.update(
        {
            "run_id": run_id,
            "gate_id": gate_id,
            "handoff_id": handoff_id if accepted else None,
            "ack_result_path": str(ack_dir / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_RESULT.json"),
            "ack_report_path": str(ack_dir / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REPORT.md"),
            "run_record_path": str(run_path),
            "gate_path": str(gate_path),
            "handoff_path": str(handoff_path) if accepted else None,
            "handoff_in_rel": rel_handoff(_latest_summary_handoff(task)),
            "handoff_out_rel": f"handoffs/{handoff_path.name}" if accepted else "none",
        }
    )


def _write_ack_artifacts(ack: dict[str, Any]) -> None:
    Path(ack["ack_result_path"]).write_text(json.dumps(ack, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(ack["ack_report_path"]).write_text(render_supervisor_summary_ack_report(ack), encoding="utf-8")
    Path(ack["run_record_path"]).write_text(render_run_record(ack), encoding="utf-8")
    Path(ack["gate_path"]).write_text(render_gate_record(ack), encoding="utf-8")
    if ack.get("handoff_path"):
        Path(ack["handoff_path"]).write_text(render_handoff_record(ack), encoding="utf-8")


def _approval_attempts(summary: dict[str, Any], ledger: dict[str, Any], task: Path) -> list[str]:
    attempts: list[str] = []
    records: list[tuple[str, dict[str, Any]]] = [("summary", summary), ("ledger", ledger)]
    for path_key in ("run_record_path", "gate_path", "handoff_path"):
        value = summary.get(path_key)
        if value and Path(value).exists():
            records.append((str(value), load_frontmatter(value)))
    for label, payload in records:
        attempts.extend(_attempts_in_payload(label, payload))
    return attempts


def _attempts_in_payload(label: str, payload: dict[str, Any]) -> list[str]:
    attempts: list[str] = []
    keys = ["final_evidence_approved", "final_verdict_frozen", "solver_approved", "odb_metrics_approved", "task_final_evidence_ledger_updated"]
    for key in keys:
        if payload.get(key) is True:
            attempts.append(f"{label}: {key}=true")
    flags = payload.get("safety_flags") or payload.get("forbidden_actions") or {}
    if isinstance(flags, dict):
        for key in keys:
            if flags.get(key) is True:
                attempts.append(f"{label}: flags.{key}=true")
    for index, entry in enumerate(payload.get("entries", []) if isinstance(payload.get("entries"), list) else []):
        if isinstance(entry, dict):
            for key in keys:
                if entry.get(key) is True:
                    attempts.append(f"{label}: entries[{index}].{key}=true")
    return attempts


def _blocked_status_for_summary_errors(errors: list[str]) -> str:
    joined = " ".join(errors)
    if "final_evidence_approved" in joined or "final_verdict_frozen" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"
    if "solver_approved" in joined or "odb_metrics_approved" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"
    if "task_final_evidence_ledger_updated" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION"
    return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_INVALID_SUMMARY"


def _blocked_status_for_ledger_errors(errors: list[str]) -> str:
    joined = " ".join(errors)
    if "final evidence approval" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"
    if "solver or ODB metrics approval" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"
    return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_LEDGER_INVALID"


def _blocked_status_for_approval_attempts(errors: list[str]) -> str:
    joined = " ".join(errors)
    if "task_final_evidence_ledger_updated" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION"
    if "final_evidence_approved" in joined or "final_verdict_frozen" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"
    if "solver_approved" in joined or "odb_metrics_approved" in joined:
        return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"
    return "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_INVALID_SUMMARY"


def _sha256_or_none(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _latest_summary_handoff(task: Path) -> str | None:
    candidates = sorted((task / "handoffs").glob("*EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY_TO_PIPELINE_SUPERVISOR.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return str(candidates[0]) if candidates else None


def _next_available_id(directory: Path, prefix: str, start: int) -> str:
    number = start
    while any(directory.glob(f"{prefix}_{number:03d}_*.md")):
        number += 1
    return f"{prefix}_{number:03d}"


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


def _command_result(task: Path, ack: dict[str, Any], success: bool) -> dict[str, Any]:
    return {
        "command": "supervisor-ack-non-solver-summary",
        "verdict": ack["ack_status"],
        "success": success,
        "errors": ack.get("fail_items", []) if not success else [],
        "warnings": ack.get("warning_items", []),
        "output_paths": {
            "ack_result": ack.get("ack_result_path"),
            "ack_report": ack.get("ack_report_path"),
            "run_record": ack.get("run_record_path"),
            "gate": ack.get("gate_path"),
            "handoff": ack.get("handoff_path"),
            "ack_ledger_md": ack.get("ack_ledger_md_path"),
            "ack_ledger_json": ack.get("ack_ledger_json_path"),
        },
        "details": ack | {"task_dir": str(task)},
    }
