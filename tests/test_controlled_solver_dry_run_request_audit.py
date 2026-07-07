from abqpilot.gui.controlled_solver_dry_run_request_audit import audit_controlled_solver_dry_run_request_no_execution


def test_dry_run_request_audit_passes_clean_task(tmp_path) -> None:
    task = tmp_path / "task"
    task.mkdir()
    audit = audit_controlled_solver_dry_run_request_no_execution(task, {"solver_run": False, "request_active": False})
    assert audit["audit_status"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT_PASS"
    assert audit["no_solver_request_files_found"] is True
    assert audit["no_output_execution_dir_found"] is True


def test_dry_run_request_audit_fails_active_request(tmp_path) -> None:
    task = tmp_path / "task"
    task.mkdir()
    (task / "solver_request.json").write_text("{}", encoding="utf-8")
    audit = audit_controlled_solver_dry_run_request_no_execution(task, {})
    assert audit["audit_status"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT_FAIL"
