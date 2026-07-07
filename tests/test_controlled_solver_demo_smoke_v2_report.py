from abqpilot.gui.controlled_solver_demo_smoke_v2_report import render_demo_smoke_v2_audit, render_demo_smoke_v2_report


def test_demo_smoke_v2_report_mentions_boundaries() -> None:
    report = render_demo_smoke_v2_report({"verdict": "PASS_STAGE5_3A_V2_CONTROLLED_SOLVER_DEMO_SMOKE_INFRA_READY_SOLVER_NOT_RUN_ENV_UNAVAILABLE", "source_inp_path": "source.inp", "copied_inp_path": "demo_solver_smoke.inp", "status": {"solver_invoked": False, "solver_status": "STAGE5_3A_V2_BLOCKED_ABAQUS_COMMAND_NOT_FOUND", "solver_return_code": None, "odb_produced": False, "odb_opened": False, "metrics_extracted": False, "final_evidence_approved": False}})
    assert "controlled Abaqus demo invocation" in report
    assert "No ODB is opened" in report
    assert "Metrics are not extracted" in report
    assert "Final evidence remains locked" in report


def test_demo_smoke_v2_audit_report_renders_checks() -> None:
    report = render_demo_smoke_v2_audit({"audit_status": "STAGE5_3A_V2_SAFETY_AUDIT_PASS", "checks": {"odb_not_opened": True}})
    assert "STAGE5_3A_V2_SAFETY_AUDIT_PASS" in report
    assert "odb_not_opened" in report
