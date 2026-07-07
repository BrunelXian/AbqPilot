from abqpilot.gui.controlled_solver_dry_run_request_report import render_dry_run_request_audit, render_dry_run_request_report


def test_dry_run_request_report_copy() -> None:
    text = render_dry_run_request_report({"dry_run_request": {"dry_run_only": True, "request_active": False}})
    assert "Dry-run request artifact only; not an active solver_request.json" in text
    assert "No output execution directory is created" in text


def test_dry_run_request_audit_report_copy() -> None:
    text = render_dry_run_request_audit({"audit_status": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT_PASS", "checks": {"no_solver_request_files_found": True}})
    assert "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT_PASS" in text
