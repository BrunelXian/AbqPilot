from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from abqpilot.pipeline_protocol.frontmatter import load_frontmatter


class GuiWorkflowState(StrEnum):
    NO_TASK_SELECTED = "GUI_STATE_NO_TASK_SELECTED"
    TASK_SCAFFOLDED = "GUI_STATE_TASK_SCAFFOLDED"
    ACOM_HANDOFF_READY = "GUI_STATE_ACOM_HANDOFF_READY"
    ACOM_RESULT_PENDING_INTAKE = "GUI_STATE_ACOM_RESULT_PENDING_INTAKE"
    ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION = "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"
    REVALIDATION_SCAFFOLD_READY = "GUI_STATE_REVALIDATION_SCAFFOLD_READY"
    NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR = "GUI_STATE_NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR"
    SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER = "GUI_STATE_SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER"
    NON_SOLVER_SUMMARY_READY_PENDING_ACK = "GUI_STATE_NON_SOLVER_SUMMARY_READY_PENDING_ACK"
    NON_SOLVER_SUMMARY_ACKNOWLEDGED = "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED"
    BLOCKED = "GUI_STATE_BLOCKED"
    REVIEW_REQUIRED = "GUI_STATE_REVIEW_REQUIRED"


FORBIDDEN_GUI_STATE_TOKENS = {
    "FINAL_EVIDENCE_APPROVED",
    "FINAL_VERDICT_FROZEN",
    "SOLVER_APPROVED",
    "ODB_APPROVED",
    "METRICS_APPROVED",
}


@dataclass(frozen=True)
class PipelineRecordSummary:
    count: int
    latest_path: str | None = None
    latest_id: str | None = None
    latest_status: str | None = None
    latest_decision: str | None = None


@dataclass(frozen=True)
class GuiWorkflowInspection:
    task_dir: str | None
    task_id: str | None
    state: str
    current_stage_label: str
    latest_status: str | None
    next_safe_action: str
    blocked_actions: list[str]
    warning_messages: list[str]
    non_final_boundary: str
    final_evidence_locked: bool
    high_risk_actions_disabled: bool
    task_exists: bool
    trace_index_exists: bool
    codex_handoff_exists: bool
    codex_structured_result_exists: bool
    acom_result_intake_exists: bool
    revalidation_package_exists: bool
    revalidation_execution_result_exists: bool
    supervisor_review_result_exists: bool
    non_solver_evidence_ledger_exists: bool
    non_solver_summary_result_exists: bool
    supervisor_summary_ack_result_exists: bool
    non_solver_summary_ack_ledger_exists: bool
    task_final_evidence_ledger_locked: bool
    run_records: PipelineRecordSummary
    handoff_records: PipelineRecordSummary
    gate_records: PipelineRecordSummary
    artifact_paths: dict[str, str | None] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["run_records"] = asdict(self.run_records)
        payload["handoff_records"] = asdict(self.handoff_records)
        payload["gate_records"] = asdict(self.gate_records)
        return payload


def inspect_gui_workflow_state(task_dir: str | Path | None) -> dict[str, Any]:
    return classify_task_workflow_state(task_dir).to_dict()


def classify_task_workflow_state(task_dir: str | Path | None) -> GuiWorkflowInspection:
    if task_dir is None:
        return _empty_inspection(None, GuiWorkflowState.NO_TASK_SELECTED, "No task selected", "Load or scaffold a task.")

    task = Path(task_dir)
    if not task.exists():
        return _empty_inspection(str(task), GuiWorkflowState.NO_TASK_SELECTED, "Task missing", "Load an existing task directory.")

    task_id = task.name
    run_records = _record_summary(task / "trace", "RUN_*.md", "run_id", "status")
    handoff_records = _record_summary(task / "handoffs", "HANDOFF_*.md", "handoff_id", "target_run")
    gate_records = _record_summary(task / "gates", "GATE_*.md", "gate_id", "decision")

    artifacts = _artifact_paths(task)
    flags = {key: Path(path).exists() if path else False for key, path in artifacts.items()}
    revalidation_result = _latest_file(task / "revalidation", "REVALIDATION_EXECUTION_RESULT.json")
    revalidation_scaffold = _latest_file(task / "revalidation", "REVALIDATION_SCAFFOLD.json")
    flags["revalidation_execution_result"] = revalidation_result is not None
    flags["revalidation_package"] = revalidation_scaffold is not None or (task / "revalidation").exists()

    latest_status: str | None = None
    state = GuiWorkflowState.TASK_SCAFFOLDED
    current_stage_label = "Task scaffolded"
    next_safe_action = "Generate Pipeline ACOM Handoff"
    warnings: list[str] = []

    ack_result = _read_json(artifacts["supervisor_summary_ack_result"])
    if _status_in(ack_result, "ack_status", {"SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED_WITH_WARNINGS"}):
        latest_status = str(ack_result.get("ack_status"))
        state = GuiWorkflowState.NON_SOLVER_SUMMARY_ACKNOWLEDGED
        current_stage_label = "PipelineSupervisor summary acknowledgement"
        next_safe_action = "DocsStatusAgent status sync remains non-final."
    else:
        summary_result = _read_json(artifacts["non_solver_summary_result"])
        if _status_in(summary_result, "summary_status", {"NON_SOLVER_EVIDENCE_SUMMARY_READY", "NON_SOLVER_EVIDENCE_SUMMARY_READY_WITH_WARNINGS"}):
            latest_status = str(summary_result.get("summary_status"))
            state = GuiWorkflowState.NON_SOLVER_SUMMARY_READY_PENDING_ACK
            current_stage_label = "EvidenceReportAgent non-solver summary ready"
            next_safe_action = "Supervisor Ack Non-Solver Summary"
        else:
            supervisor_review = _read_json(artifacts["supervisor_review_result"])
            if _status_in(
                supervisor_review,
                "review_status",
                {
                    "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER",
                    "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_WITH_WARNINGS_FOR_LEDGER",
                },
            ):
                latest_status = str(supervisor_review.get("review_status"))
                state = GuiWorkflowState.SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER
                current_stage_label = "PipelineSupervisor review accepted for non-solver ledger"
                next_safe_action = "Generate Non-Solver Evidence Summary"
            elif revalidation_result is not None:
                revalidation_payload = _read_json(str(revalidation_result))
                latest_status = str(revalidation_payload.get("result_status") or revalidation_payload.get("status") or "")
                if latest_status in {
                    "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
                    "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR",
                }:
                    state = GuiWorkflowState.NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR
                    current_stage_label = "Non-solver revalidation pending supervisor"
                    next_safe_action = "Supervisor Review Non-Solver Revalidation"
                elif "BLOCKED" in latest_status or "FAIL" in latest_status:
                    state = GuiWorkflowState.BLOCKED
                    current_stage_label = "Non-solver revalidation blocked"
                    next_safe_action = "Review blocked result before continuing."
                    warnings.append(latest_status)
                else:
                    state = GuiWorkflowState.REVIEW_REQUIRED
                    current_stage_label = "Non-solver revalidation requires review"
                    next_safe_action = "Report Non-Solver Revalidation"
            elif flags["revalidation_package"]:
                state = GuiWorkflowState.REVALIDATION_SCAFFOLD_READY
                current_stage_label = "Downstream revalidation scaffold ready"
                latest_status = _scaffold_status(revalidation_scaffold)
                next_safe_action = "Execute Non-Solver Revalidation"
            elif flags["acom_result_intake"]:
                intake = _read_json(artifacts["acom_result_intake"])
                latest_status = str(
                    intake.get("pipeline_intake_status")
                    or intake.get("intake_status")
                    or intake.get("status")
                    or intake.get("verdict")
                    or ""
                )
                if latest_status == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION" or "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION" in json.dumps(intake):
                    state = GuiWorkflowState.ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION
                    current_stage_label = "ACOM result accepted pending revalidation"
                    next_safe_action = "Scaffold ACOM Revalidation"
                elif "REJECTED" in latest_status:
                    state = GuiWorkflowState.BLOCKED
                    current_stage_label = "ACOM result intake blocked"
                    next_safe_action = "Inspect intake report."
                else:
                    state = GuiWorkflowState.REVIEW_REQUIRED
                    current_stage_label = "ACOM result intake requires review"
                    next_safe_action = "Report ACOM Result Intake"
            elif flags["codex_structured_result"]:
                state = GuiWorkflowState.ACOM_RESULT_PENDING_INTAKE
                current_stage_label = "ACOM structured result pending intake"
                latest_status = "structured_result.json present"
                next_safe_action = "Intake ACOM Result"
            elif flags["codex_handoff"]:
                state = GuiWorkflowState.ACOM_HANDOFF_READY
                current_stage_label = "ACOM handoff ready"
                latest_status = "codex_handoff present"
                next_safe_action = "External Codex operator may produce structured_result.json; AbqPilot does not run Codex."
            elif not flags["trace_index"]:
                state = GuiWorkflowState.REVIEW_REQUIRED
                current_stage_label = "Task exists without TRACE_INDEX.md"
                latest_status = run_records.latest_status or gate_records.latest_decision
                next_safe_action = "Validate Pipeline Protocol"

    if any(token in state.value for token in FORBIDDEN_GUI_STATE_TOKENS):
        raise ValueError(f"forbidden GUI workflow state: {state.value}")

    return GuiWorkflowInspection(
        task_dir=str(task),
        task_id=task_id,
        state=state.value,
        current_stage_label=current_stage_label,
        latest_status=latest_status or run_records.latest_status or gate_records.latest_decision,
        next_safe_action=next_safe_action,
        blocked_actions=[
            "Run Solver",
            "Open ODB",
            "Queue Job",
            "Run Codex",
            "Auto Schedule Agent",
            "Approve Final Evidence",
            "Freeze Final Verdict",
            "Approve Solver / ODB / Metrics",
        ],
        warning_messages=warnings,
        non_final_boundary="Non-final / non-solver record. Final evidence remains locked.",
        final_evidence_locked=True,
        high_risk_actions_disabled=True,
        task_exists=True,
        trace_index_exists=flags["trace_index"],
        codex_handoff_exists=flags["codex_handoff"],
        codex_structured_result_exists=flags["codex_structured_result"],
        acom_result_intake_exists=flags["acom_result_intake"],
        revalidation_package_exists=flags["revalidation_package"],
        revalidation_execution_result_exists=flags["revalidation_execution_result"],
        supervisor_review_result_exists=flags["supervisor_review_result"],
        non_solver_evidence_ledger_exists=flags["non_solver_evidence_ledger"],
        non_solver_summary_result_exists=flags["non_solver_summary_result"],
        supervisor_summary_ack_result_exists=flags["supervisor_summary_ack_result"],
        non_solver_summary_ack_ledger_exists=flags["non_solver_summary_ack_ledger"],
        task_final_evidence_ledger_locked=True,
        run_records=run_records,
        handoff_records=handoff_records,
        gate_records=gate_records,
        artifact_paths=artifacts | {
            "latest_revalidation_result": str(revalidation_result) if revalidation_result else None,
            "latest_revalidation_scaffold": str(revalidation_scaffold) if revalidation_scaffold else None,
        },
    )


def _empty_inspection(
    task_dir: str | None,
    state: GuiWorkflowState,
    label: str,
    next_action: str,
) -> GuiWorkflowInspection:
    return GuiWorkflowInspection(
        task_dir=task_dir,
        task_id=None,
        state=state.value,
        current_stage_label=label,
        latest_status=None,
        next_safe_action=next_action,
        blocked_actions=["Run Solver", "Open ODB", "Queue Job", "Run Codex", "Approve Final Evidence", "Freeze Final Verdict"],
        warning_messages=[],
        non_final_boundary="Non-final / non-solver record. Final evidence remains locked.",
        final_evidence_locked=True,
        high_risk_actions_disabled=True,
        task_exists=False,
        trace_index_exists=False,
        codex_handoff_exists=False,
        codex_structured_result_exists=False,
        acom_result_intake_exists=False,
        revalidation_package_exists=False,
        revalidation_execution_result_exists=False,
        supervisor_review_result_exists=False,
        non_solver_evidence_ledger_exists=False,
        non_solver_summary_result_exists=False,
        supervisor_summary_ack_result_exists=False,
        non_solver_summary_ack_ledger_exists=False,
        task_final_evidence_ledger_locked=True,
        run_records=PipelineRecordSummary(0),
        handoff_records=PipelineRecordSummary(0),
        gate_records=PipelineRecordSummary(0),
    )


def _artifact_paths(task: Path) -> dict[str, str | None]:
    return {
        "trace_index": str(task / "TRACE_INDEX.md"),
        "codex_handoff": str(task / "codex_handoff"),
        "codex_structured_result": str(task / "codex_result" / "structured_result.json"),
        "acom_result_intake": str(task / "codex_result" / "acom_result_intake.json"),
        "supervisor_review_result": str(task / "supervisor_review" / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json"),
        "non_solver_evidence_ledger": str(task / "NON_SOLVER_EVIDENCE_LEDGER.json"),
        "non_solver_summary_result": str(task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"),
        "supervisor_summary_ack_result": str(task / "supervisor_summary_ack" / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_RESULT.json"),
        "non_solver_summary_ack_ledger": str(task / "NON_SOLVER_SUMMARY_ACK_LEDGER.json"),
        "task_final_evidence_ledger": str(task / "TASK_FINAL_EVIDENCE_LEDGER.md"),
    }


def _record_summary(folder: Path, pattern: str, id_key: str, status_key: str) -> PipelineRecordSummary:
    files = sorted(folder.glob(pattern)) if folder.exists() else []
    if not files:
        return PipelineRecordSummary(count=0)
    latest = files[-1]
    frontmatter: dict[str, Any] = {}
    try:
        frontmatter = load_frontmatter(latest)
    except (OSError, UnicodeDecodeError):
        frontmatter = {}
    return PipelineRecordSummary(
        count=len(files),
        latest_path=str(latest),
        latest_id=str(frontmatter.get(id_key) or latest.stem.split("_", 2)[0]),
        latest_status=str(frontmatter.get(status_key) or "") or None,
        latest_decision=str(frontmatter.get("decision") or "") or None,
    )


def _latest_file(root: Path, name: str) -> Path | None:
    if not root.exists():
        return None
    files = sorted(root.rglob(name), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def _read_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    target = Path(path)
    if not target.exists() or target.is_dir():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _status_in(payload: dict[str, Any], key: str, allowed: set[str]) -> bool:
    return str(payload.get(key) or "") in allowed


def _scaffold_status(path: Path | None) -> str | None:
    if path is None:
        return None
    payload = _read_json(str(path))
    return str(payload.get("scaffold_status") or payload.get("status") or "REVALIDATION_SCAFFOLD_READY")
