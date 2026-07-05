from __future__ import annotations

from abqpilot.gui.workflow_timeline import TIMELINE_STAGES, build_workflow_timeline


def test_workflow_timeline_contains_all_non_solver_acom_stages():
    labels = [label for _, label in TIMELINE_STAGES]
    assert labels == [
        "ACOM Handoff",
        "ACOM Result Intake",
        "Revalidation Scaffold",
        "Non-Solver Revalidation",
        "Supervisor Review",
        "Non-Solver Ledger",
        "Evidence Summary",
        "Supervisor Ack",
    ]


def test_workflow_timeline_marks_acknowledged_state():
    timeline = build_workflow_timeline({"state": "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED"})
    assert len(timeline) == 8
    assert timeline[-1]["status"] == "ACKNOWLEDGED"
