from __future__ import annotations

import json
from pathlib import Path

from abqpilot.gui.trace_viewer import TraceViewerState, build_trace_viewer


SMOKE_TASK = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")


def test_trace_viewer_module_imports():
    assert TraceViewerState.READY.value == "TRACE_VIEWER_READY"


def test_stage5_0i_smoke_task_trace_viewer_ready():
    viewer = build_trace_viewer(SMOKE_TASK)
    assert viewer["viewer_state"] == "TRACE_VIEWER_READY"
    assert len(viewer["timeline_steps"]) == 8
    assert viewer["read_only"] is True


def test_fresh_scaffold_trace_viewer_no_trace_records(tmp_path):
    task = tmp_path / "fresh"
    task.mkdir()
    (task / "TRACE_INDEX.md").write_text("---\ndoc_type: trace_index\ntask_id: fresh\nstatus: SCAFFOLDED\n---\n", encoding="utf-8")
    viewer = build_trace_viewer(task)
    assert viewer["viewer_state"] == "TRACE_VIEWER_NO_TRACE_RECORDS"


def test_missing_task_trace_viewer_task_not_found(tmp_path):
    viewer = build_trace_viewer(tmp_path / "missing")
    assert viewer["viewer_state"] == "TRACE_VIEWER_TASK_NOT_FOUND"


def test_trace_viewer_groups_run_handoff_gate_records():
    viewer = build_trace_viewer(SMOKE_TASK)
    assert viewer["trace_records"]["runs"]
    assert viewer["trace_records"]["handoffs"]
    assert viewer["trace_records"]["gates"]
    for group in ("runs", "handoffs", "gates"):
        assert "read_only_path" in viewer["trace_records"][group][0]


def test_trace_viewer_flags_unsafe_final_claims(tmp_path):
    task = tmp_path / "unsafe"
    (task / "codex_result").mkdir(parents=True)
    (task / "codex_result" / "acom_result_intake.json").write_text(
        json.dumps({"final_evidence_approved": True}, indent=2),
        encoding="utf-8",
    )
    viewer = build_trace_viewer(task)
    assert viewer["viewer_state"] == "TRACE_VIEWER_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
    assert viewer["unsafe_claims"][0]["key"] == "final_evidence_approved"


def test_trace_viewer_flags_solver_and_odb_claims(tmp_path):
    task = tmp_path / "unsafe_solver"
    (task / "supervisor_review").mkdir(parents=True)
    (task / "supervisor_review" / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json").write_text(
        json.dumps({"solver_approved": True, "odb_metrics_approved": True}, indent=2),
        encoding="utf-8",
    )
    viewer = build_trace_viewer(task)
    keys = {claim["key"] for claim in viewer["unsafe_claims"]}
    assert "solver_approved" in keys
    assert "odb_metrics_approved" in keys


def test_trace_viewer_flags_final_verdict_frozen(tmp_path):
    task = tmp_path / "unsafe_verdict"
    (task / "evidence_report").mkdir(parents=True)
    (task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json").write_text(
        json.dumps({"final_verdict_frozen": True}, indent=2),
        encoding="utf-8",
    )
    viewer = build_trace_viewer(task)
    assert viewer["viewer_state"] == "TRACE_VIEWER_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
