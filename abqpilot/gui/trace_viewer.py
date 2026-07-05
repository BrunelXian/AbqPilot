from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from abqpilot.gui.evidence_file_resolver import resolve_evidence_files
from abqpilot.gui.pipeline_trace_view import build_pipeline_trace_view
from abqpilot.gui.preview_safety import UNSAFE_PREVIEW_CLAIM_KEYS
from abqpilot.gui.read_only_document_view import build_read_only_document_view
from abqpilot.gui.workflow_timeline import TIMELINE_STAGES, build_workflow_timeline
from abqpilot.gui.workflow_state import inspect_gui_workflow_state


class TraceViewerState(StrEnum):
    NO_TASK_SELECTED = "TRACE_VIEWER_NO_TASK_SELECTED"
    TASK_NOT_FOUND = "TRACE_VIEWER_TASK_NOT_FOUND"
    NO_TRACE_RECORDS = "TRACE_VIEWER_NO_TRACE_RECORDS"
    READY = "TRACE_VIEWER_READY"
    READY_WITH_MISSING_FILES = "TRACE_VIEWER_READY_WITH_MISSING_FILES"
    BLOCKED_INVALID_FRONTMATTER = "TRACE_VIEWER_BLOCKED_INVALID_FRONTMATTER"
    BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM = "TRACE_VIEWER_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
    REVIEW_REQUIRED = "TRACE_VIEWER_REVIEW_REQUIRED"


class TimelineStepStatus(StrEnum):
    NOT_STARTED = "TIMELINE_STEP_NOT_STARTED"
    READY = "TIMELINE_STEP_READY"
    PENDING = "TIMELINE_STEP_PENDING"
    WARNING = "TIMELINE_STEP_WARNING"
    BLOCKED = "TIMELINE_STEP_BLOCKED"
    ACKNOWLEDGED = "TIMELINE_STEP_ACKNOWLEDGED"
    MISSING = "TIMELINE_STEP_MISSING"
    REVIEW_REQUIRED = "TIMELINE_STEP_REVIEW_REQUIRED"


UNSAFE_CLAIM_KEYS = set(UNSAFE_PREVIEW_CLAIM_KEYS)


STEP_RECORD_KEYWORDS = {
    "acom_handoff": ("ACOM_", "ACOM_TO_CODEX_OPERATOR"),
    "acom_result_intake": ("ACOM_RESULT",),
    "revalidation_scaffold": ("REVALIDATION.md", "REVALIDATION_TO_PIPELINE_SUPERVISOR"),
    "non_solver_revalidation": ("REVALIDATION_RESULT", "REVALIDATION_EXECUTION"),
    "supervisor_review": ("SUPERVISOR_NON_SOLVER_REVIEW",),
    "non_solver_ledger": ("NON_SOLVER_EVIDENCE_LEDGER", "SUPERVISOR_NON_SOLVER_REVIEW"),
    "evidence_summary": ("EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY", "NON_SOLVER_EVIDENCE_SUMMARY"),
    "supervisor_ack": ("SUPERVISOR_NON_SOLVER_SUMMARY_ACK", "NON_SOLVER_SUMMARY_ACK"),
}


def build_trace_viewer(task_dir: str | Path | None) -> dict[str, Any]:
    if task_dir is None:
        return _empty_viewer(TraceViewerState.NO_TASK_SELECTED.value, None)
    task = Path(task_dir)
    if not task.exists():
        return _empty_viewer(TraceViewerState.TASK_NOT_FOUND.value, str(task))

    workflow = inspect_gui_workflow_state(task)
    trace = build_pipeline_trace_view(task)
    timeline = build_workflow_timeline(workflow)
    evidence = resolve_evidence_files(task)
    grouped_records = _group_records(trace)
    unsafe_claims = _collect_unsafe_claims(task, grouped_records, evidence)
    steps = [_build_step(task, stage_id, label, timeline, grouped_records, evidence) for stage_id, label in TIMELINE_STAGES]

    record_count = sum(len(grouped_records[key]) for key in ("runs", "handoffs", "gates"))
    missing_started_files = [
        item
        for step in steps
        if step["status"] not in {TimelineStepStatus.NOT_STARTED.value, TimelineStepStatus.MISSING.value}
        for item in step["missing_expected_files"]
    ]
    if unsafe_claims:
        state = TraceViewerState.BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM.value
    elif record_count == 0:
        state = TraceViewerState.NO_TRACE_RECORDS.value
    elif missing_started_files:
        state = TraceViewerState.READY_WITH_MISSING_FILES.value
    else:
        state = TraceViewerState.READY.value

    return {
        "schema_version": "0.1",
        "stage": "Stage 5.1C",
        "viewer_state": state,
        "task_dir": str(task),
        "task_id": task.name,
        "timeline_steps": steps,
        "trace_records": grouped_records,
        "unsafe_claims": unsafe_claims,
        "claim_boundary": "Read-only trace viewer. Non-solver summary acknowledgement is non-final.",
        "safety_boundary": "Timeline selection does not execute actions. Final evidence remains locked. Solver / ODB / metrics are disabled. Codex output is displayed as structured input, not final evidence.",
        "read_only": True,
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
    }


def _empty_viewer(state: str, task_dir: str | None) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.1C",
        "viewer_state": state,
        "task_dir": task_dir,
        "task_id": None,
        "timeline_steps": [],
        "trace_records": {"runs": [], "handoffs": [], "gates": []},
        "unsafe_claims": [],
        "claim_boundary": "Read-only trace viewer.",
        "safety_boundary": "Timeline selection does not execute actions. Final evidence remains locked.",
        "read_only": True,
    }


def _build_step(
    task: Path,
    step_id: str,
    label: str,
    timeline: list[dict[str, str]],
    grouped_records: dict[str, list[dict[str, Any]]],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    timeline_item = next((item for item in timeline if item["stage_id"] == step_id), None) or {}
    raw_status = str(timeline_item.get("status") or "not started")
    status = _normalize_step_status(raw_status)
    records = _related_records(step_id, grouped_records)
    artifacts = evidence.get(step_id, {"json_files": [], "markdown_files": [], "missing": []})
    latest_gate = records["related_gate_files"][-1] if records["related_gate_files"] else None
    latest_run = records["related_run_files"][-1] if records["related_run_files"] else None
    latest_handoff = records["related_handoff_files"][-1] if records["related_handoff_files"] else None
    latest_decision = _frontmatter_value(latest_gate, "decision")
    latest_verdict = _frontmatter_value(latest_run, "status")
    return {
        "step_id": step_id,
        "display_name": label,
        "status": status,
        "badge": timeline_item.get("badge"),
        "related_run_files": records["related_run_files"],
        "related_handoff_files": records["related_handoff_files"],
        "related_gate_files": records["related_gate_files"],
        "related_json_files": artifacts.get("json_files", []),
        "related_markdown_reports": records["related_markdown_reports"] + artifacts.get("markdown_files", []),
        "latest_decision": latest_decision,
        "latest_verdict": latest_verdict,
        "latest_handoff_target": _frontmatter_value(latest_handoff, "to_agent"),
        "claim_boundary": "Non-final / non-solver trace evidence only.",
        "safety_boundary": "Selecting this step is read-only and does not execute actions.",
        "missing_expected_files": artifacts.get("missing", []) if status != TimelineStepStatus.NOT_STARTED.value else [],
        "selectable": True,
        "read_only": True,
        "action_allowed": False,
    }


def _group_records(trace: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "runs": [_record_item(item) for item in trace.get("runs", [])],
        "handoffs": [_record_item(item) for item in trace.get("handoffs", [])],
        "gates": [_record_item(item) for item in trace.get("gates", [])],
    }


def _record_item(item: dict[str, Any]) -> dict[str, Any]:
    view = build_read_only_document_view(item.get("path"), max_lines=20)
    frontmatter = view.get("frontmatter", {})
    return {
        "filename": Path(str(item.get("path", ""))).name,
        "path": item.get("path"),
        "doc_type": item.get("doc_type") or frontmatter.get("doc_type"),
        "id": item.get("id"),
        "agent": item.get("agent") or frontmatter.get("agent"),
        "status": item.get("status") or frontmatter.get("status") or frontmatter.get("decision"),
        "decision": frontmatter.get("decision"),
        "risk_level": frontmatter.get("risk_level"),
        "final_evidence_approved": frontmatter.get("final_evidence_approved"),
        "final_verdict_frozen": frontmatter.get("final_verdict_frozen"),
        "read_only_path": item.get("path"),
        "frontmatter": frontmatter,
    }


def _related_records(step_id: str, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    keywords = STEP_RECORD_KEYWORDS.get(step_id, ())
    related_runs = _filter_paths(grouped["runs"], keywords)
    related_handoffs = _filter_paths(grouped["handoffs"], keywords)
    related_gates = _filter_paths(grouped["gates"], keywords)
    return {
        "related_run_files": related_runs,
        "related_handoff_files": related_handoffs,
        "related_gate_files": related_gates,
        "related_markdown_reports": related_runs + related_handoffs + related_gates,
    }


def _filter_paths(records: list[dict[str, Any]], keywords: tuple[str, ...]) -> list[str]:
    paths: list[str] = []
    for record in records:
        haystack = f"{record.get('filename')} {record.get('path')} {record.get('status')} {record.get('decision')}"
        if any(keyword in haystack for keyword in keywords):
            paths.append(str(record["path"]))
    return paths


def _normalize_step_status(status: str) -> str:
    upper = status.upper().replace(" ", "_")
    if upper == "NOT_STARTED":
        return TimelineStepStatus.NOT_STARTED.value
    if upper in {"READY", "PASS"}:
        return TimelineStepStatus.READY.value
    if upper == "PENDING":
        return TimelineStepStatus.PENDING.value
    if upper == "WARNING":
        return TimelineStepStatus.WARNING.value
    if upper == "BLOCKED":
        return TimelineStepStatus.BLOCKED.value
    if upper == "ACKNOWLEDGED":
        return TimelineStepStatus.ACKNOWLEDGED.value
    if upper == "MISSING":
        return TimelineStepStatus.MISSING.value
    return TimelineStepStatus.REVIEW_REQUIRED.value


def _frontmatter_value(path: str | None, key: str) -> Any:
    if not path:
        return None
    return build_read_only_document_view(path, max_lines=1).get("frontmatter", {}).get(key)


def _collect_unsafe_claims(task: Path, grouped_records: dict[str, list[dict[str, Any]]], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for record_group in grouped_records.values():
        for record in record_group:
            claims.extend(_unsafe_claims_in_payload(str(record.get("path")), record.get("frontmatter", {})))
    for step in evidence.values():
        for path in step.get("json_files", []):
            payload = build_read_only_document_view(path).get("frontmatter", {})
            claims.extend(_unsafe_claims_in_payload(path, payload))
    task_final = task / "TASK_FINAL_EVIDENCE_LEDGER.md"
    if task_final.exists():
        view = build_read_only_document_view(task_final)
        claims.extend(_unsafe_claims_in_payload(str(task_final), view.get("frontmatter", {})))
    return claims


def _unsafe_claims_in_payload(path: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for key in UNSAFE_CLAIM_KEYS:
        if payload.get(key) is True:
            claims.append({"path": path, "key": key, "value": True})
    safety_flags = payload.get("safety_flags")
    if isinstance(safety_flags, dict):
        for key in UNSAFE_CLAIM_KEYS:
            if safety_flags.get(key) is True:
                claims.append({"path": path, "key": f"safety_flags.{key}", "value": True})
    return claims
