from __future__ import annotations

from typing import Any

from abqpilot.gui.high_risk_gate_catalog import get_high_risk_gate_catalog
from abqpilot.gui.high_risk_prerequisites import get_prerequisites_for_action


def build_high_risk_gate_checklists() -> list[dict[str, Any]]:
    checklists: list[dict[str, Any]] = []
    for action in get_high_risk_gate_catalog():
        checklists.append(
            {
                "action_id": action["action_id"],
                "display_name": action["display_name"],
                "preview_only": True,
                "approval_status": "NOT_APPROVED",
                "execution_status": "NOT_EXECUTABLE",
                "prerequisites": get_prerequisites_for_action(str(action["action_id"])),
                "stage_5_2a_instruction": "Prerequisites shown here are advisory/specification only.",
            }
        )
    return checklists
