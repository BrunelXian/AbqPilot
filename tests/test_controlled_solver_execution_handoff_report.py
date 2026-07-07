from abqpilot.gui.controlled_solver_execution_handoff_report import (
    render_execution_handoff_draft_markdown,
    render_execution_handoff_report,
    render_no_execution_audit,
)


def test_execution_handoff_reports_include_no_execution_copy() -> None:
    draft = {
        "source_task_id": "stage5_2f_controlled_solver_real_gate_smoke",
        "source_gate_id": "GATE_001",
        "source_gate_decision": "APPROVED_BY_HUMAN",
        "candidate_artifact_path": "candidate.inp",
        "candidate_artifact_hash": "abc",
        "candidate_hash_verified": True,
        "from_agent": "PipelineSupervisor",
        "to_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "draft_only": True,
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
        "execution_status": "NOT_EXECUTABLE",
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
    validation = {"validation_status": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_READY"}
    audit = {"audit_status": "CONTROLLED_SOLVER_HANDOFF_DRAFT_NO_EXECUTION_AUDIT_PASS", "checks": {"no_solver_request_files_found": True}}
    md = render_execution_handoff_draft_markdown(draft, validation)
    report = render_execution_handoff_report({"draft": draft, "validation": validation, "no_execution_audit": audit})
    audit_md = render_no_execution_audit(audit)
    assert "Draft only; not an active execution handoff" in md
    assert "No solver request file is created" in md
    assert "Final evidence remains locked" in md
    assert "future ExecutionAgent handoff" in report
    assert "No solver request" in audit_md
