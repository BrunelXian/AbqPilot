from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.acom.non_solver_evidence_summary_report import (
    rel_handoff,
    render_cli_summary_report,
    render_gate_record,
    render_handoff_record,
    render_non_solver_summary_report,
    render_run_record,
)
from abqpilot.acom.non_solver_evidence_summary_schema import (
    READY_GATE,
    READY_STATUS,
    READY_WARNINGS_GATE,
    READY_WARNINGS_STATUS,
    SCHEMA_VERSION,
    STAGE,
    validate_non_solver_evidence_summary,
    validate_non_solver_ledger,
)
from abqpilot.pipeline_protocol.protocol_report import generate_protocol_report
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


def generate_non_solver_evidence_summary(
    task_dir: str | Path,
    ledger_json: str | Path | None = None,
    summary_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    summary = _build_summary(task, ledger_json, summary_id)
    _assign_pipeline_records(task, summary, accepted=summary["gate_decision"] != "BLOCKED")
    _write_summary_artifacts(summary)
    protocol = validate_task_protocol(task)
    summary["protocol_validation"] = protocol.get("verdict")
    if not protocol.get("success") and summary["gate_decision"] != "BLOCKED":
        summary["summary_status"] = "NON_SOLVER_EVIDENCE_SUMMARY_REVIEW_REQUIRED"
        summary["gate_decision"] = "BLOCKED"
        summary["blocked_items"].extend(protocol.get("errors", []))
        summary["handoff_id"] = None
        summary["handoff_path"] = None
        summary["handoff_out_rel"] = "none"
    valid, schema_errors = validate_non_solver_evidence_summary(summary)
    if not valid and summary["gate_decision"] != "BLOCKED":
        summary["summary_status"] = "NON_SOLVER_EVIDENCE_SUMMARY_REVIEW_REQUIRED"
        summary["gate_decision"] = "BLOCKED"
        summary["blocked_items"].extend(schema_errors)
        summary["handoff_id"] = None
        summary["handoff_path"] = None
        summary["handoff_out_rel"] = "none"
    _write_summary_artifacts(summary)
    return _command_result(task, summary, success=summary["summary_status"] in {READY_STATUS, READY_WARNINGS_STATUS})


def report_non_solver_evidence_summary(
    task_dir: str | Path,
    ledger_json: str | Path | None = None,
    summary_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    result_path = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"
    if not result_path.exists():
        return {
            "command": "report-non-solver-evidence-summary",
            "verdict": "NON_SOLVER_EVIDENCE_SUMMARY_REPORT_MISSING",
            "success": False,
            "errors": ["missing non-solver evidence summary result"],
            "warnings": [],
            "output_paths": {},
            "details": {"task_dir": str(task)},
        }
    summary = json.loads(result_path.read_text(encoding="utf-8"))
    report_path = task / "NON_SOLVER_EVIDENCE_SUMMARY_CLI_REPORT.md"
    protocol = generate_protocol_report(task)
    report_path.write_text(
        render_cli_summary_report(summary) + f"\n## Pipeline Protocol\n`{protocol.get('validation_verdict')}`\n",
        encoding="utf-8",
    )
    return {
        "command": "report-non-solver-evidence-summary",
        "verdict": "NON_SOLVER_EVIDENCE_SUMMARY_REPORT_READY",
        "success": True,
        "errors": [],
        "warnings": summary.get("warning_items", []),
        "output_paths": {"report_path": str(report_path), "summary_result": str(result_path)},
        "details": summary | {"protocol_validation": protocol.get("validation_verdict")},
    }


def _build_summary(task: Path, ledger_json: str | Path | None, summary_id: str | None) -> dict[str, Any]:
    ledger_json_path = Path(ledger_json) if ledger_json else task / "NON_SOLVER_EVIDENCE_LEDGER.json"
    ledger_md_path = task / "NON_SOLVER_EVIDENCE_LEDGER.md"
    entries: list[dict[str, Any]] = []
    checks: list[dict[str, str]] = []
    warnings: list[str] = []
    blocked: list[str] = []
    status = READY_STATUS
    gate = READY_GATE

    def check(name: str, ok: bool, detail: str, *, warning: bool = False) -> None:
        state = "pass" if ok else ("warning" if warning else "fail")
        checks.append({"name": name, "status": state, "detail": detail})
        if state == "warning":
            warnings.append(f"{name}: {detail}")
        elif state == "fail":
            blocked.append(f"{name}: {detail}")

    if not ledger_json_path.exists() or not ledger_md_path.exists():
        status = "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_MISSING_LEDGER"
        gate = "BLOCKED"
        check("ledger exists", False, f"missing {ledger_json_path if not ledger_json_path.exists() else ledger_md_path}")
        ledger_payload: dict[str, Any] = {}
    else:
        check("ledger exists", True, "NON_SOLVER_EVIDENCE_LEDGER.md/json found")
        try:
            ledger_payload = json.loads(ledger_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            ledger_payload = {}
            status = "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_LEDGER_INVALID"
            gate = "BLOCKED"
            check("ledger JSON parses", False, str(exc))
        else:
            valid, ledger_errors, ledger_warnings = validate_non_solver_ledger(ledger_payload)
            entries = ledger_payload.get("entries", []) if isinstance(ledger_payload.get("entries"), list) else []
            if not entries:
                status = "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_EMPTY_LEDGER"
                gate = "BLOCKED"
            elif not valid:
                status = _blocked_status_for_ledger_errors(ledger_errors)
                gate = "BLOCKED"
            elif ledger_warnings:
                status = READY_WARNINGS_STATUS
                gate = READY_WARNINGS_GATE
            check("ledger schema and entries valid", valid, "; ".join(ledger_errors) if ledger_errors else "valid")
            for item in ledger_warnings:
                check("ledger entry warning", True, item, warning=True)
    source_records = _collect_source_records(task, entries)
    source_block = _source_approval_attempts(source_records)
    if source_block:
        status = _blocked_status_for_approval_attempts(source_block)
        gate = "BLOCKED"
        check("source records do not claim approval", False, "; ".join(source_block))
    elif entries and gate != "BLOCKED":
        check("source records do not claim approval", True, "no final/solver/ODB approval attempt found")
    lineage = _lineage(task, entries, source_records)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": task.name,
        "task_dir": str(task),
        "summary_id": summary_id or "latest",
        "summary_status": status,
        "gate_decision": gate,
        "ledger_json_path": str(ledger_json_path),
        "ledger_md_path": str(ledger_md_path),
        "ledger_entries": entries,
        "entries_reviewed": len(entries),
        "source_records_reviewed": source_records,
        "lineage": lineage,
        "checks": checks,
        "warning_items": warnings,
        "blocked_items": blocked,
        "summary_scope": "non-final non-solver evidence summary",
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "task_final_evidence_ledger_updated": False,
        "codex_summary_is_final_evidence": False,
        "next_action": "PipelineSupervisor acknowledgement is required; do not freeze final evidence.",
        "safety_flags": _safe_flags(),
    }


def _write_summary_artifacts(summary: dict[str, Any]) -> None:
    Path(summary["summary_result_path"]).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(summary["summary_report_path"]).write_text(render_non_solver_summary_report(summary), encoding="utf-8")
    Path(summary["run_record_path"]).write_text(render_run_record(summary), encoding="utf-8")
    Path(summary["gate_path"]).write_text(render_gate_record(summary), encoding="utf-8")
    if summary.get("handoff_path"):
        Path(summary["handoff_path"]).write_text(render_handoff_record(summary), encoding="utf-8")


def _assign_pipeline_records(task: Path, summary: dict[str, Any], *, accepted: bool) -> None:
    evidence_dir = task / "evidence_report"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for child in ("trace", "handoffs", "gates"):
        (task / child).mkdir(parents=True, exist_ok=True)
    run_id = _next_available_id(task / "trace", "RUN", 19)
    gate_id = _next_available_id(task / "gates", "GATE", 15)
    handoff_id = _next_available_id(task / "handoffs", "HANDOFF", 18)
    run_path = task / "trace" / f"{run_id}_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md"
    gate_path = task / "gates" / f"{gate_id}_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md"
    handoff_path = task / "handoffs" / f"{handoff_id}_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY_TO_PIPELINE_SUPERVISOR.md"
    summary.update(
        {
            "run_id": run_id,
            "gate_id": gate_id,
            "handoff_id": handoff_id if accepted else None,
            "summary_result_path": str(evidence_dir / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"),
            "summary_report_path": str(evidence_dir / "NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md"),
            "run_record_path": str(run_path),
            "gate_path": str(gate_path),
            "handoff_path": str(handoff_path) if accepted else None,
            "handoff_in_rel": rel_handoff(_latest_supervisor_handoff(task)),
            "handoff_out_rel": f"handoffs/{handoff_path.name}" if accepted else "none",
        }
    )


def _collect_source_records(task: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    candidates: set[Path] = set()
    review = task / "supervisor_review" / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json"
    if review.exists():
        candidates.add(review)
    for entry in entries:
        for raw in entry.get("artifacts_reviewed", []):
            if raw and str(raw).endswith(".json"):
                path = Path(raw)
                if path.exists():
                    candidates.add(path)
    for path in sorted(candidates, key=lambda item: str(item)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        records.append({"path": str(path), "payload": payload})
    return records


def _source_approval_attempts(records: list[dict[str, Any]]) -> list[str]:
    keys = ["final_evidence_approved", "final_verdict_frozen", "solver_approved", "odb_metrics_approved"]
    attempts: list[str] = []
    for record in records:
        payload = record.get("payload", {})
        for key in keys:
            if payload.get(key) is True:
                attempts.append(f"{record.get('path')}: {key}=true")
        flags = payload.get("safety_flags") or {}
        if isinstance(flags, dict):
            for key in keys:
                if flags.get(key) is True:
                    attempts.append(f"{record.get('path')}: safety_flags.{key}=true")
    return attempts


def _blocked_status_for_ledger_errors(errors: list[str]) -> str:
    joined = " ".join(errors)
    if "final evidence approval" in joined:
        return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"
    if "solver or ODB metrics approval" in joined:
        return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"
    if "must be" in joined or "missing fields" in joined:
        return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_LEDGER_INVALID"
    return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_UNSAFE_ENTRY"


def _blocked_status_for_approval_attempts(errors: list[str]) -> str:
    joined = " ".join(errors)
    if "final_evidence_approved" in joined or "final_verdict_frozen" in joined:
        return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"
    if "solver_approved" in joined or "odb_metrics_approved" in joined:
        return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"
    return "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_UNSAFE_ENTRY"


def _lineage(task: Path, entries: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, list[str]]:
    artifact_paths = [str(path) for entry in entries for path in entry.get("artifacts_reviewed", []) if path]
    record_paths = [record["path"] for record in records]
    all_paths = artifact_paths + record_paths
    return {
        "acom_handoff_artifacts": sorted({str(path) for path in (task / "handoffs").glob("*ACOM*.md")}),
        "acom_intake_artifacts": sorted({path for path in all_paths if "acom_result_intake" in path or "codex_result" in path}),
        "revalidation_artifacts": sorted({path for path in all_paths if "REVALIDATION_EXECUTION" in path or "\\revalidation\\" in path or "/revalidation/" in path}),
        "supervisor_review_artifacts": sorted({path for path in all_paths if "SUPERVISOR_NON_SOLVER_REVIEW" in path or "supervisor_review" in path}),
        "pipeline_records": sorted({str(path) for folder in ("trace", "handoffs", "gates") for path in (task / folder).glob("*.md")}),
    }


def _latest_supervisor_handoff(task: Path) -> str | None:
    candidates = sorted((task / "handoffs").glob("*SUPERVISOR_NON_SOLVER_REVIEW_TO_EVIDENCE_REPORT_AGENT.md"), key=lambda path: path.stat().st_mtime, reverse=True)
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


def _command_result(task: Path, summary: dict[str, Any], success: bool) -> dict[str, Any]:
    return {
        "command": "generate-non-solver-evidence-summary",
        "verdict": summary["summary_status"],
        "success": success,
        "errors": summary.get("blocked_items", []) if not success else [],
        "warnings": summary.get("warning_items", []),
        "output_paths": {
            "summary_result": summary.get("summary_result_path"),
            "summary_report": summary.get("summary_report_path"),
            "run_record": summary.get("run_record_path"),
            "gate": summary.get("gate_path"),
            "handoff": summary.get("handoff_path"),
        },
        "details": summary | {"task_dir": str(task)},
    }
