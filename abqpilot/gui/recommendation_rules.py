from __future__ import annotations

from enum import StrEnum
from typing import Any


class NextStepStatus(StrEnum):
    NO_TASK_SELECTED = "NEXT_STEP_NO_TASK_SELECTED"
    READY = "NEXT_STEP_READY"
    READY_WITH_WARNINGS = "NEXT_STEP_READY_WITH_WARNINGS"
    WAITING_FOR_EXTERNAL_CODEX_RESULT = "NEXT_STEP_WAITING_FOR_EXTERNAL_CODEX_RESULT"
    PENDING_REVALIDATION = "NEXT_STEP_PENDING_REVALIDATION"
    PENDING_SUPERVISOR_REVIEW = "NEXT_STEP_PENDING_SUPERVISOR_REVIEW"
    PENDING_SUMMARY_ACK = "NEXT_STEP_PENDING_SUMMARY_ACK"
    NON_SOLVER_WORKFLOW_ACKNOWLEDGED = "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED"
    BLOCKED = "NEXT_STEP_BLOCKED"
    REVIEW_REQUIRED = "NEXT_STEP_REVIEW_REQUIRED"


HIGH_RISK_DOWNSTREAM_AGENTS = {
    "GuardAgent",
    "CandidateBuilderAgent",
    "DiagnosisAgent",
    "ExecutionAgent",
    "MetricsAgent",
}


LOW_RISK_DOWNSTREAM_AGENTS = {
    "DocsStatusAgent",
    "SoftwareQAAgent",
    "AuditAgent",
    "EvidenceReportAgent",
    "PipelineSupervisor",
}


def recommendation_for_workflow_state(
    workflow_state: dict[str, Any],
    *,
    downstream_agent: str | None = None,
) -> dict[str, Any]:
    state = str(workflow_state.get("state") or "GUI_STATE_NO_TASK_SELECTED")
    base = {
        "current_state": state,
        "current_stage_label": workflow_state.get("current_stage_label"),
        "latest_status": workflow_state.get("latest_status"),
        "latest_gate_decision": workflow_state.get("gate_records", {}).get("latest_decision"),
        "prerequisites": [],
        "missing_prerequisites": [],
        "expected_outputs": [],
        "warnings": list(workflow_state.get("warning_messages", [])),
        "blocked_reasons": [],
        "risk_level": "LOW",
        "final_evidence_effect": "NONE",
        "action_allowed": False,
        "auto_execute_allowed": False,
        "codex_execution_allowed": False,
        "solver_approved": False,
        "odb_approved": False,
        "metrics_approved": False,
    }
    mapping = {
        "GUI_STATE_NO_TASK_SELECTED": _no_task,
        "GUI_STATE_TASK_SCAFFOLDED": _task_scaffolded,
        "GUI_STATE_ACOM_HANDOFF_READY": _acom_handoff_ready,
        "GUI_STATE_ACOM_RESULT_PENDING_INTAKE": _acom_result_pending_intake,
        "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION": _acom_result_accepted,
        "GUI_STATE_REVALIDATION_SCAFFOLD_READY": lambda payload: _revalidation_scaffold_ready(payload, downstream_agent),
        "GUI_STATE_NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR": _pending_supervisor,
        "GUI_STATE_SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER": _supervisor_review_accepted,
        "GUI_STATE_NON_SOLVER_SUMMARY_READY_PENDING_ACK": _summary_ready_pending_ack,
        "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED": _summary_acknowledged,
        "GUI_STATE_BLOCKED": _blocked,
        "GUI_STATE_REVIEW_REQUIRED": _review_required,
    }
    result = mapping.get(state, _review_required)(base)
    _enforce_safe_result(result)
    return result


def _no_task(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.NO_TASK_SELECTED.value,
        recommended_action_id="scaffold_pipeline_task",
        recommended_action_label="Select or scaffold a task workspace",
        recommended_panel="Task Workspace",
        recommendation_rationale="A task workspace is required before ACOM/non-solver records can be inspected.",
        prerequisites=["Project root is loaded"],
        expected_outputs=["Selected task directory or scaffolded pipeline task"],
        user_instruction="Load an existing task or use the Task Workspace scaffold action.",
    )
    return payload


def _task_scaffolded(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.READY.value,
        recommended_action_id="generate_pipeline_acom_handoff",
        recommended_action_label="Generate Pipeline ACOM Handoff",
        recommended_panel="ACOM Handoff",
        recommendation_rationale="The task exists and can receive a bounded ACOM handoff package.",
        prerequisites=["Task directory", "Pipeline scaffold"],
        expected_outputs=["codex_handoff/", "RUN/HANDOFF records for ACOM handoff"],
        user_instruction="Use the ACOM Handoff panel. Do not run Codex from the GUI.",
    )
    return payload


def _acom_handoff_ready(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.WAITING_FOR_EXTERNAL_CODEX_RESULT.value,
        recommended_action_id="validate_acom_template_pack",
        recommended_action_label="Validate/report ACOM handoff, then wait for external structured_result.json",
        recommended_panel="ACOM Handoff",
        recommendation_rationale="A handoff package exists. Codex, if used, must operate externally and return structured_result.json.",
        prerequisites=["codex_handoff/"],
        missing_prerequisites=["codex_result/structured_result.json"],
        expected_outputs=["codex_result/structured_result.json from external operator"],
        warnings=["GUI does not call Codex CLI. Codex output must return as structured_result.json for AbqPilot intake."],
        user_instruction="Review the handoff and wait for a human-operated external Codex result.",
    )
    return payload


def _acom_result_pending_intake(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.READY.value,
        recommended_action_id="intake_acom_result",
        recommended_action_label="Intake ACOM Result",
        recommended_panel="ACOM Result Intake",
        recommendation_rationale="structured_result.json exists and can be checked as input for AbqPilot revalidation.",
        prerequisites=["codex_handoff/", "codex_result/structured_result.json"],
        expected_outputs=["codex_result/acom_result_intake.json", "ACOM result RUN/GATE/HANDOFF records"],
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        user_instruction="Use the ACOM Result Intake panel; intake does not accept final evidence.",
    )
    return payload


def _acom_result_accepted(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.PENDING_REVALIDATION.value,
        recommended_action_id="scaffold_acom_revalidation",
        recommended_action_label="Scaffold ACOM Revalidation",
        recommended_panel="Downstream Revalidation",
        recommendation_rationale="The ACOM result is accepted only pending deterministic AbqPilot revalidation.",
        prerequisites=["codex_result/acom_result_intake.json"],
        expected_outputs=["revalidation/<agent>_<id>/REVALIDATION_SCAFFOLD.json", "revalidation RUN/GATE/HANDOFF records"],
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        user_instruction="Create the downstream revalidation package; do not execute high-risk agents.",
    )
    return payload


def _revalidation_scaffold_ready(payload: dict[str, Any], downstream_agent: str | None) -> dict[str, Any]:
    if downstream_agent in HIGH_RISK_DOWNSTREAM_AGENTS:
        payload.update(
            recommendation_status=NextStepStatus.REVIEW_REQUIRED.value,
            recommended_action_id="report_acom_revalidation",
            recommended_action_label="Report ACOM Revalidation and keep high-risk agent blocked",
            recommended_panel="Downstream Revalidation",
            recommendation_rationale=f"{downstream_agent} is high-risk and cannot be executed by this GUI stage.",
            prerequisites=["REVALIDATION_SCAFFOLD.json"],
            expected_outputs=["Read-only revalidation report"],
            warnings=["GuardAgent / CandidateBuilderAgent / DiagnosisAgent / ExecutionAgent / MetricsAgent are high-risk and blocked in this GUI stage."],
            blocked_reasons=[f"High-risk downstream agent blocked: {downstream_agent}"],
            user_instruction="Inspect the scaffold and wait for a future explicit guarded stage.",
        )
        return payload
    payload.update(
        recommendation_status=NextStepStatus.READY.value,
        recommended_action_id="execute_non_solver_revalidation",
        recommended_action_label="Execute Non-Solver Revalidation",
        recommended_panel="Non-Solver Revalidation Execution",
        recommendation_rationale="The scaffold is ready for a supported low-risk deterministic non-solver check.",
        prerequisites=["REVALIDATION_SCAFFOLD.json", f"low-risk downstream agent: {downstream_agent or 'unknown'}"],
        expected_outputs=["REVALIDATION_EXECUTION_RESULT.json", "REVALIDATION_EXECUTION_REPORT.md"],
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        warnings=[] if downstream_agent in LOW_RISK_DOWNSTREAM_AGENTS else ["Downstream agent not identified; review before execution."],
        user_instruction="Use the non-solver revalidation panel only for supported low-risk agents.",
    )
    if downstream_agent not in LOW_RISK_DOWNSTREAM_AGENTS:
        payload["recommendation_status"] = NextStepStatus.REVIEW_REQUIRED.value
    return payload


def _pending_supervisor(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.PENDING_SUPERVISOR_REVIEW.value,
        recommended_action_id="supervisor_review_non_solver_revalidation",
        recommended_action_label="Supervisor Review Non-Solver Revalidation",
        recommended_panel="PipelineSupervisor Review",
        recommendation_rationale="Non-solver revalidation completed and requires non-final supervisor review.",
        prerequisites=["REVALIDATION_EXECUTION_RESULT.json"],
        expected_outputs=["supervisor_review/", "NON_SOLVER_EVIDENCE_LEDGER.md/json when accepted"],
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        user_instruction="Use PipelineSupervisor Review; this does not approve final evidence.",
    )
    return payload


def _supervisor_review_accepted(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.READY.value,
        recommended_action_id="generate_non_solver_evidence_summary",
        recommended_action_label="Generate Non-Solver Evidence Summary",
        recommended_panel="EvidenceReportAgent Non-Solver Summary",
        recommendation_rationale="Supervisor accepted the result for the non-solver ledger only.",
        prerequisites=["NON_SOLVER_EVIDENCE_LEDGER.md/json"],
        expected_outputs=["evidence_report/NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json", "NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md"],
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        user_instruction="Generate the non-final non-solver summary.",
    )
    return payload


def _summary_ready_pending_ack(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.PENDING_SUMMARY_ACK.value,
        recommended_action_id="supervisor_ack_non_solver_summary",
        recommended_action_label="Supervisor Ack Non-Solver Summary",
        recommended_panel="PipelineSupervisor Summary Ack",
        recommendation_rationale="EvidenceReportAgent summary is ready and awaits non-final supervisor acknowledgement.",
        prerequisites=["evidence_report/NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"],
        expected_outputs=["supervisor_summary_ack/", "NON_SOLVER_SUMMARY_ACK_LEDGER.md/json"],
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        user_instruction="Acknowledge the non-solver summary only; final evidence remains locked.",
    )
    return payload


def _summary_acknowledged(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.NON_SOLVER_WORKFLOW_ACKNOWLEDGED.value,
        recommended_action_id="review_non_solver_summary_ack",
        recommended_action_label="Review final non-solver summary / ack ledger",
        recommended_panel="Evidence Summary / Supervisor Ack",
        recommendation_rationale="No further non-solver ACOM governance action is required for this task.",
        prerequisites=["NON_SOLVER_SUMMARY_ACK_LEDGER.md/json"],
        expected_outputs=["Read-only review only"],
        user_instruction="Continue only through a future explicit high-risk stage if solver, ODB, metrics, or final evidence is needed.",
        warnings=["Final evidence remains locked. This is not final evidence approval."],
    )
    return payload


def _blocked(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.BLOCKED.value,
        recommended_action_id="inspect_trace_and_artifacts",
        recommended_action_label="Inspect trace viewer and artifact preview",
        recommended_panel="Trace Viewer / Artifact Preview / Safety",
        recommendation_rationale="The workflow is blocked; inspect missing files, blocked records, and unsafe claims before continuing.",
        expected_outputs=["Read-only diagnosis of blocked records"],
        blocked_reasons=payload.get("warnings") or ["Workflow state is blocked"],
        user_instruction="Do not proceed until human review resolves the blocked condition.",
    )
    return payload


def _review_required(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(
        recommendation_status=NextStepStatus.REVIEW_REQUIRED.value,
        recommended_action_id="inspect_trace_and_artifacts",
        recommended_action_label="Inspect trace viewer and artifact preview",
        recommended_panel="Trace Viewer / Artifact Preview / Safety",
        recommendation_rationale="The workflow needs human review before the next safe action is clear.",
        expected_outputs=["Read-only review notes"],
        user_instruction="Review records and missing prerequisites before proceeding.",
    )
    return payload


def _enforce_safe_result(result: dict[str, Any]) -> None:
    if result.get("final_evidence_effect") in {"FINAL_EVIDENCE_APPROVAL", "FINAL_VERDICT_FREEZE"}:
        raise ValueError("unsafe final evidence effect")
    for key in ("auto_execute_allowed", "codex_execution_allowed", "solver_approved", "odb_approved", "metrics_approved"):
        if result.get(key) is True:
            raise ValueError(f"unsafe recommendation flag: {key}")
