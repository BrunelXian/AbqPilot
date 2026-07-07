from abqpilot.gui.controlled_solver_request_preflight_report import render_request_preflight_audit, render_request_preflight_report


def test_request_preflight_report_contains_no_execution_copy() -> None:
    result = {
        "source_gate_validated": True,
        "source_handoff_draft_validated": True,
        "source_request_draft_validated": True,
        "candidate_hash_verified": True,
        "solver_command_label_validated": True,
        "solver_command_path_not_invoked": True,
        "output_dir_policy_validated": True,
        "output_dir_created": False,
        "cpu_policy_validated": True,
        "memory_policy_validated": True,
        "timeout_policy_validated": True,
        "log_capture_policy_validated": True,
        "preflight_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION",
        "preflight_passed": True,
        "preflight_only": True,
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "solver_request_created": False,
        "solver_execution_allowed": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "validation": {"validation_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION"},
        "no_execution_audit": {"audit_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT_PASS"},
    }
    report = render_request_preflight_report(result)
    audit = render_request_preflight_audit({"audit_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT_PASS", "checks": {"no_solver_request_files_found": True}})
    assert "Preflight pass is not solver execution permission" in report
    assert "No solver_request.json is created" in report
    assert "No output directory for execution is created" in report
    assert "No active solver request" in audit
