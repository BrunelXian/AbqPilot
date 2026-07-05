from __future__ import annotations

from typing import Any

from abqpilot.gui.status_badges import badge


TIMELINE_STAGES = (
    ("acom_handoff", "ACOM Handoff"),
    ("acom_result_intake", "ACOM Result Intake"),
    ("revalidation_scaffold", "Revalidation Scaffold"),
    ("non_solver_revalidation", "Non-Solver Revalidation"),
    ("supervisor_review", "Supervisor Review"),
    ("non_solver_ledger", "Non-Solver Ledger"),
    ("evidence_summary", "Evidence Summary"),
    ("supervisor_ack", "Supervisor Ack"),
)


def build_workflow_timeline(workflow_state: dict[str, Any]) -> list[dict[str, str]]:
    active_state = str(workflow_state.get("state") or "")
    rank = _rank_for_state(active_state)
    timeline: list[dict[str, str]] = []
    for index, (stage_id, label) in enumerate(TIMELINE_STAGES):
        status = _stage_status(index, rank, active_state)
        timeline.append(
            {
                "stage_id": stage_id,
                "label": label,
                "status": status,
                "badge": badge(status),
            }
        )
    return timeline


def render_timeline_text(timeline: list[dict[str, str]]) -> str:
    return "\n".join(f"{item['badge']} {item['label']}" for item in timeline)


def _rank_for_state(state: str) -> int:
    mapping = {
        "GUI_STATE_ACOM_HANDOFF_READY": 0,
        "GUI_STATE_ACOM_RESULT_PENDING_INTAKE": 1,
        "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION": 1,
        "GUI_STATE_REVALIDATION_SCAFFOLD_READY": 2,
        "GUI_STATE_NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR": 3,
        "GUI_STATE_SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER": 5,
        "GUI_STATE_NON_SOLVER_SUMMARY_READY_PENDING_ACK": 6,
        "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED": 7,
    }
    return mapping.get(state, -1)


def _stage_status(index: int, rank: int, state: str) -> str:
    if "BLOCKED" in state:
        return "BLOCKED" if index == max(rank, 0) else "not started"
    if rank < 0:
        return "not started"
    if index < rank:
        return "READY"
    if index == rank:
        if state.endswith("ACKNOWLEDGED"):
            return "ACKNOWLEDGED"
        if "PENDING" in state:
            return "PENDING"
        return "READY"
    return "not started"
