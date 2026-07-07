from pathlib import Path


def test_stage5_2j_docs_and_gui_imports() -> None:
    import abqpilot.gui.app  # noqa: F401
    import abqpilot.gui.controlled_solver_dry_run_request  # noqa: F401
    import abqpilot.gui.controlled_solver_dry_run_request_audit  # noqa: F401
    import abqpilot.gui.controlled_solver_dry_run_request_card  # noqa: F401
    import abqpilot.gui.controlled_solver_dry_run_request_report  # noqa: F401
    import abqpilot.gui.controlled_solver_dry_run_request_validator  # noqa: F401

    text = Path("docs/CONTROLLED_SOLVER_EXECUTION_DRY_RUN_REQUEST_MATERIALIZATION.md").read_text(encoding="utf-8")
    assert "dry-run-only controlled solver request artifact" in text
    assert "not named `solver_request.json`" in text
    assert "Dry-run request materialization is not execution permission" in text
    assert "TASK_FINAL_EVIDENCE_LEDGER.md" in text
