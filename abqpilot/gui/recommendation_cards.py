from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.next_step_recommender import build_next_step_recommendation
from abqpilot.gui.recommendation_copy import (
    CODEX_EXTERNAL_COPY,
    FINAL_EVIDENCE_LOCKED_COPY,
    NON_FINAL_WORKFLOW_COPY,
    RECOMMENDATION_ONLY_NOTICE,
    SOLVER_ODB_METRICS_DISABLED_COPY,
)
from abqpilot.gui.status_badges import status_badge


def build_next_step_recommendation_card(task_dir: str | Path | None) -> dict[str, Any]:
    recommendation = build_next_step_recommendation(task_dir)
    return {
        "title": "Recommended Next Step",
        "status_badge": status_badge(str(recommendation.get("recommendation_status"))),
        "current_state": recommendation.get("current_state"),
        "recommended_action_label": recommendation.get("recommended_action_label"),
        "recommended_panel": recommendation.get("recommended_panel"),
        "rationale": recommendation.get("recommendation_rationale"),
        "prerequisites": recommendation.get("prerequisites", []),
        "missing_prerequisites": recommendation.get("missing_prerequisites", []),
        "expected_outputs": recommendation.get("expected_outputs", []),
        "safety_notes": recommendation.get("safety_notes", []),
        "disabled_actions": recommendation.get("disabled_actions_summary", []),
        "final_evidence_effect": recommendation.get("final_evidence_effect"),
        "read_only_notice": RECOMMENDATION_ONLY_NOTICE,
        "auto_execute_notice": "auto_execute_allowed=false",
        "user_instruction": recommendation.get("user_instruction"),
        "copy": [
            RECOMMENDATION_ONLY_NOTICE,
            FINAL_EVIDENCE_LOCKED_COPY,
            NON_FINAL_WORKFLOW_COPY,
            CODEX_EXTERNAL_COPY,
            SOLVER_ODB_METRICS_DISABLED_COPY,
        ],
        "recommendation": recommendation,
        "action_allowed": False,
        "auto_execute_allowed": False,
        "read_only": True,
    }


def render_next_step_recommendation_text(card: dict[str, Any]) -> str:
    lines = [
        str(card.get("title")),
        str(card.get("status_badge")),
        "",
        "Current State",
        str(card.get("current_state")),
        "",
        "Recommendation",
        f"Use panel: {card.get('recommended_panel')}",
        f"Action: {card.get('recommended_action_label')}",
        "",
        "Rationale",
        str(card.get("rationale")),
        "",
        "Prerequisites",
    ]
    lines.extend(f"- {item}" for item in card.get("prerequisites", []))
    missing = card.get("missing_prerequisites", [])
    if missing:
        lines.extend(["", "Missing Prerequisites"])
        lines.extend(f"- {item}" for item in missing)
    lines.extend(["", "Expected Outputs"])
    lines.extend(f"- {item}" for item in card.get("expected_outputs", []))
    lines.extend(
        [
            "",
            "Final Evidence Effect",
            str(card.get("final_evidence_effect")),
            "",
            "Safety Notes",
        ]
    )
    lines.extend(f"- {item}" for item in card.get("safety_notes", []))
    lines.extend(["", "Disabled Actions"])
    for item in card.get("disabled_actions", [])[:8]:
        lines.append(f"- {item.get('display_name')}: {item.get('disabled_reason')}")
    lines.extend(
        [
            "",
            "User Instruction",
            str(card.get("user_instruction")),
            "",
            "Claim Boundary",
            "Recommendation only; no automatic execution",
            "Final evidence remains locked",
            "Non-final / non-solver workflow",
            "GUI does not call Codex CLI",
            "Solver / ODB / metrics remain disabled",
        ]
    )
    return "\n".join(lines)
