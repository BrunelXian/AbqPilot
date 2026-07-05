from __future__ import annotations

from typing import Any

from abqpilot.gui.controlled_solver_inactive_gate_card import build_controlled_solver_inactive_gate_card
from abqpilot.gui.high_risk_gate_catalog import get_high_risk_gate_catalog
from abqpilot.gui.controlled_solver_gate_card import build_controlled_solver_gate_card
from abqpilot.gui.safe_action_catalog import group_actions_by_panel


PANEL_ALIASES = {
    "Task Workspace": "Setup / Task",
    "ACOM Handoff": "ACOM",
    "ACOM Result Intake": "Result Intake",
    "Downstream Revalidation": "Revalidation",
    "Non-Solver Revalidation Execution": "Revalidation",
    "PipelineSupervisor Review": "Supervisor",
    "PipelineSupervisor Summary Ack": "Supervisor",
    "EvidenceReportAgent Non-Solver Summary": "Evidence Summary",
    "Pipeline Trace": "Reports",
    "Disabled High-Risk Actions": "Safety / Disabled",
}


def build_action_panels() -> list[dict[str, Any]]:
    raw = group_actions_by_panel()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for panel, actions in raw.items():
        grouped.setdefault(PANEL_ALIASES.get(panel, panel), []).extend(actions)
    return [
        {
            "panel": panel,
            "actions": actions,
            "has_disabled_actions": any(not action.get("allowed") for action in actions),
        }
        for panel, actions in grouped.items()
    ]


def disabled_actions_have_no_callbacks() -> bool:
    for panel in build_action_panels():
        for action in panel["actions"]:
            if not action.get("allowed") and action.get("backend_method") is not None:
                return False
    return True


def build_high_risk_gate_panel() -> dict[str, Any]:
    return {
        "panel": "High-Risk Gates",
        "preview_only": True,
        "no_execution_notice": "Preview only; not an approval. No high-risk action is executable in Stage 5.2A.",
        "actions": [
            {
                "action_id": action["action_id"],
                "display_name": action["display_name"],
                "risk_level": action["risk_level"],
                "allowed": False,
                "executable": False,
                "preview_only": True,
                "requires_future_stage": True,
                "requires_human_gate": True,
                "disabled_reason": action["disabled_reason"],
                "backend_method": None,
                "final_evidence_effect": action["final_evidence_effect"],
            }
            for action in get_high_risk_gate_catalog()
        ],
    }


def build_controlled_solver_gate_panel(task_dir: str | None = None) -> dict[str, Any]:
    card = build_controlled_solver_gate_card(task_dir)
    inactive_card = build_controlled_solver_inactive_gate_card(task_dir)
    return {
        "panel": "Controlled Solver Gate Preview",
        "preview_only": True,
        "no_execution_notice": "Preview only; not a solver approval. No Abaqus solver command is executed.",
        "card": card,
        "inactive_gate_draft_card": inactive_card,
        "actions": [
            {
                "action_id": "preview_controlled_solver_gate_requirements",
                "display_name": "Preview Controlled Solver Gate Requirements",
                "allowed": True,
                "executable": False,
                "preview_only": True,
                "backend_method": None,
                "final_evidence_effect": "PREVIEW_ONLY",
            },
            {
                "action_id": "preview_controlled_solver_inactive_gate_draft",
                "display_name": "Preview Controlled Solver Inactive Gate Draft",
                "allowed": True,
                "executable": False,
                "preview_only": True,
                "backend_method": None,
                "final_evidence_effect": "PREVIEW_ONLY",
            }
        ],
    }
