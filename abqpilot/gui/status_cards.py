from __future__ import annotations

from typing import Any

from abqpilot.gui.safe_action_catalog import get_safe_action_catalog
from abqpilot.gui.status_badges import badge, status_badge


def build_project_header_card(presenter: dict[str, Any]) -> dict[str, Any]:
    state = presenter["workflow_state"]
    project = presenter["sections"].get("Project Status", {})
    return {
        "title": "AbqPilot-v2",
        "workflow_family": "Stage 5 non-solver ACOM governance",
        "current_accepted_verdict": project.get("current_accepted_verdict"),
        "current_task_state_badge": status_badge(state.get("latest_status")),
        "badges": [
            badge("LOCKED", "Final evidence remains locked"),
            badge("DISABLED", "Solver / ODB / Metrics disabled"),
            badge("NON_FINAL", "Non-final / non-solver workflow"),
        ],
    }


def build_task_workspace_card(presenter: dict[str, Any]) -> dict[str, Any]:
    state = presenter["workflow_state"]
    return {
        "selected_task_directory": state.get("task_dir"),
        "task_id": state.get("task_id"),
        "task_scaffold_status": "ready" if state.get("trace_index_exists") else "missing trace index",
        "latest_workflow_state": state.get("state"),
        "latest_run": state.get("run_records", {}).get("latest_path"),
        "latest_gate": state.get("gate_records", {}).get("latest_path"),
        "latest_handoff": state.get("handoff_records", {}).get("latest_path"),
        "counts": {
            "RUN": state.get("run_records", {}).get("count"),
            "HANDOFF": state.get("handoff_records", {}).get("count"),
            "GATE": state.get("gate_records", {}).get("count"),
        },
    }


def build_next_safe_action_card(presenter: dict[str, Any]) -> dict[str, Any]:
    state = presenter["workflow_state"]
    action = _find_action_by_display(str(state.get("next_safe_action") or ""))
    final_effect = str(action.get("final_evidence_effect") if action else "NONE")
    if final_effect not in {"NONE", "NON_FINAL_NON_SOLVER_RECORD_ONLY"}:
        final_effect = "NONE"
    return {
        "title": "Next Safe Action",
        "next_safe_action": state.get("next_safe_action"),
        "why_safe": "Uses Stage 5.1A safe workflow state and catalog; no solver, ODB, queue, Codex execution, scheduling, or final evidence approval.",
        "requires_task_dir": bool(action.get("requires_task_dir")) if action else True,
        "expected_output": action.get("expected_cli_equivalent") if action else "read-only or non-final workflow artifact",
        "final_evidence_effect": final_effect,
    }


def build_disabled_actions_card(presenter: dict[str, Any]) -> dict[str, Any]:
    actions = presenter["sections"].get("Disabled High-Risk Actions", {}).get("actions", [])
    return {
        "title": "Disabled High-Risk Actions",
        "copy": "Disabled actions are visible for clarity and have no executable backend callback.",
        "actions": [
            {
                "display_name": action.get("display_name"),
                "badge": badge("DISABLED"),
                "disabled_reason": action.get("disabled_reason"),
                "backend_method": action.get("backend_method"),
            }
            for action in actions
        ],
    }


def build_trace_summary_card(presenter: dict[str, Any]) -> dict[str, Any]:
    state = presenter["workflow_state"]
    return {
        "title": "RUN / HANDOFF / GATE Summary",
        "run_count": state["run_records"]["count"],
        "handoff_count": state["handoff_records"]["count"],
        "gate_count": state["gate_records"]["count"],
        "latest_status": state.get("latest_status"),
        "latest_decision": state["gate_records"].get("latest_decision"),
        "blocked_reason": "; ".join(state.get("warning_messages", [])) or None,
    }


def _find_action_by_display(display_name: str) -> dict[str, Any] | None:
    for action in get_safe_action_catalog():
        if action.get("display_name") == display_name:
            return action
    return None
