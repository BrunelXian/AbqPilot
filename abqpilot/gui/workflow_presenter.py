from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.gui.pipeline_trace_view import build_pipeline_trace_view
from abqpilot.gui.safe_action_catalog import group_actions_by_panel
from abqpilot.gui.status_badges import safety_badges, status_badge
from abqpilot.gui.task_workspace_view import build_task_workspace_view
from abqpilot.gui.workflow_state import inspect_gui_workflow_state
from abqpilot.gui.workflow_timeline import build_workflow_timeline, render_timeline_text


def build_gui_workflow_presenter(task_dir: str | Path | None, project_root: str | Path | None = None) -> dict[str, Any]:
    state = inspect_gui_workflow_state(task_dir)
    task = Path(task_dir) if task_dir is not None else None
    workspace = build_task_workspace_view(task) if task is not None else build_task_workspace_view(None)
    trace = build_pipeline_trace_view(task) if task is not None and task.exists() else {"runs": [], "handoffs": [], "gates": []}
    actions = group_actions_by_panel()
    project_status = _read_project_status(project_root)
    sections = {
        "Project Status": {
            "current_accepted_verdict": project_status.get("latest_verdict"),
            "test_baseline": _extract_test_baseline(project_status),
            "final_evidence_locked": True,
            "solver_odb_metrics_locked": True,
            "copy": "Final evidence remains locked. Solver, ODB, metrics, and model mutation are disabled in this stage.",
        },
        "Task Workspace": workspace,
        "Pipeline Trace": {
            "run_count": len(trace["runs"]),
            "handoff_count": len(trace["handoffs"]),
            "gate_count": len(trace["gates"]),
            "latest_decision": state["gate_records"]["latest_decision"],
            "records": trace,
        },
        "ACOM Handoff": {"actions": actions.get("ACOM Handoff", [])},
        "ACOM Result Intake": {"actions": actions.get("ACOM Result Intake", [])},
        "Downstream Revalidation": {
            "actions": actions.get("Downstream Revalidation", []),
            "high_risk_agent_warning": "GuardAgent, CandidateBuilderAgent, DiagnosisAgent, ExecutionAgent, and MetricsAgent are blocked in Stage 5.1A GUI.",
        },
        "Non-Solver Revalidation Execution": {"actions": actions.get("Non-Solver Revalidation Execution", [])},
        "PipelineSupervisor Review": {
            "actions": actions.get("PipelineSupervisor Review", []),
            "copy": "Supervisor review accepts non-solver records only. It does not freeze final evidence.",
        },
        "EvidenceReportAgent Non-Solver Summary": {
            "actions": actions.get("EvidenceReportAgent Non-Solver Summary", []),
            "ledger_state": {
                "NON_SOLVER_EVIDENCE_LEDGER": state["non_solver_evidence_ledger_exists"],
                "NON_SOLVER_SUMMARY_ACK_LEDGER": state["non_solver_summary_ack_ledger_exists"],
                "TASK_FINAL_EVIDENCE_LEDGER": "locked / not updated",
            },
        },
        "PipelineSupervisor Summary Ack": {
            "actions": actions.get("PipelineSupervisor Summary Ack", []),
            "copy": "Supervisor acknowledgement is non-final and non-solver only.",
        },
        "Safety / Audit Status": {
            "badges": safety_badges(),
            "non_final_boundary": state["non_final_boundary"],
            "codex_result_copy": "Codex results require AbqPilot revalidation.",
        },
        "Disabled High-Risk Actions": {"actions": actions.get("Disabled High-Risk Actions", [])},
    }
    timeline = build_workflow_timeline(state)
    return {
        "workflow_state": state,
        "status_badge": status_badge(state["latest_status"]),
        "workflow_timeline": timeline,
        "workflow_timeline_text": render_timeline_text(timeline),
        "sections": sections,
    }


def render_workflow_presenter_text(presenter: dict[str, Any]) -> str:
    state = presenter["workflow_state"]
    lines = [
        "Workflow State",
        str(state["state"]),
        "",
        "Current Stage",
        str(state["current_stage_label"]),
        "",
        "Latest Status",
        str(state["latest_status"]),
        "",
        "Next Safe Action",
        str(state["next_safe_action"]),
        "",
        "Claim Boundary",
        "Non-final / non-solver record",
        "Final evidence remains locked",
        "Supervisor acknowledgement does not freeze final verdict",
        "Solver, ODB, metrics, and model mutation are disabled in this stage",
        "Codex executes externally; GUI does not call Codex CLI",
        "Accepted ACOM result means accepted for AbqPilot revalidation, not evidence",
        "",
        "Workflow Timeline",
        str(presenter.get("workflow_timeline_text") or ""),
        "",
        "Pipeline Counts",
        f"RUN={state['run_records']['count']} HANDOFF={state['handoff_records']['count']} GATE={state['gate_records']['count']}",
        "",
        "Disabled High-Risk Actions",
    ]
    lines.extend(f"- {item}" for item in state["blocked_actions"])
    return "\n".join(lines)


def _read_project_status(project_root: str | Path | None) -> dict[str, Any]:
    if project_root is None:
        return {}
    path = Path(project_root) / "PROJECT_STATUS_CURRENT.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_test_baseline(project_status: dict[str, Any]) -> str | None:
    limitations = project_status.get("known_limitations", [])
    for item in limitations if isinstance(limitations, list) else []:
        if isinstance(item, str) and "passed" in item:
            return item
    return None
