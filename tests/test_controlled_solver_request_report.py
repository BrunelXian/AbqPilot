from abqpilot.gui.controlled_solver_request_report import (
    render_request_draft_report,
    render_request_draft_schema_markdown,
    render_request_no_execution_audit,
)


def test_request_reports_include_required_copy() -> None:
    draft = {
        "source_gate_id": "GATE_001",
        "source_gate_decision": "APPROVED_BY_HUMAN",
        "source_handoff_draft_validated": True,
        "candidate_hash_verified": True,
        "target_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "solver_command_label": "ABQ2024_FUTURE_CONTROLLED_SOLVER_STAGE",
        "allowed_output_dir_preview": "future",
        "draft_only": True,
        "request_active": False,
        "executable_request": False,
        "solver_command_path_included": False,
        "solver_command_not_invoked": True,
        "output_dir_created": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
    validation = {"validation_status": "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_READY"}
    audit = {"audit_status": "CONTROLLED_SOLVER_REQUEST_DRAFT_NO_EXECUTION_AUDIT_PASS", "checks": {"no_solver_request_files_found": True}}
    md = render_request_draft_schema_markdown(draft, validation)
    report = render_request_draft_report({"draft": draft, "validation": validation, "no_execution_audit": audit, "draft_created": True})
    audit_md = render_request_no_execution_audit(audit)
    assert "Draft schema only; not an active solver request" in md
    assert "No solver_request.json is created" in md
    assert "No job request is created" in md
    assert "Final evidence remains locked" in md
    assert "does not create an active solver request" in report
    assert "No active solver request" in audit_md
