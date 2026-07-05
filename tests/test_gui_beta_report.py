from abqpilot.gui.beta_report import render_gui_beta_smoke_report


def test_gui_beta_report_includes_required_safety_copy() -> None:
    report = render_gui_beta_smoke_report(
        {
            "verdict": "PASS",
            "gui_beta_ready": True,
            "generated_at": "now",
            "smoke_cases": [{"case_id": "no_task", "passed": True, "expected": "A", "observed": "A"}],
            "component_checks": {"workflow_state": True},
            "final_evidence_approved": False,
            "final_verdict_frozen": False,
            "solver_approved": False,
            "odb_metrics_approved": False,
            "codex_cli_called": False,
            "queue_runner_launched": False,
            "auto_execute_allowed": False,
            "known_limitations": [],
        }
    )
    assert "GUI beta readiness for non-solver ACOM governance" in report
    assert "This is not final evidence approval" in report
    assert "Final evidence remains locked" in report
    assert "GUI does not call Codex CLI" in report
    assert "Recommendations are advisory; no automatic execution" in report
