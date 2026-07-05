from pathlib import Path

from abqpilot.gui.beta_smoke import build_gui_beta_e2e_smoke, write_gui_beta_e2e_smoke_outputs
from abqpilot.gui.gui_e2e_smoke import build_gui_e2e_smoke_view


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "runs" / "tasks" / "stage5_0f_non_solver_revalidation_smoke"


def test_gui_beta_smoke_modules_import() -> None:
    assert callable(build_gui_beta_e2e_smoke)
    assert callable(build_gui_e2e_smoke_view)


def test_gui_beta_smoke_covers_required_cases() -> None:
    result = build_gui_beta_e2e_smoke(ROOT, task_dir=TASK)
    cases = {case["case_id"]: case for case in result["smoke_cases"]}
    required = {
        "no_task",
        "fresh_scaffold",
        "acom_handoff_ready",
        "acom_result_pending_intake",
        "acom_result_accepted_pending_revalidation",
        "revalidation_scaffold_low_risk",
        "revalidation_scaffold_high_risk",
        "non_solver_revalidation_pending_supervisor",
        "supervisor_review_accepted",
        "summary_ready_pending_ack",
        "summary_acknowledged",
        "live_stage5_0i_summary_acknowledged",
        "unsafe_final_approval_fixture",
    }
    assert required <= set(cases)
    assert cases["acom_handoff_ready"]["observed"] == "NEXT_STEP_WAITING_FOR_EXTERNAL_CODEX_RESULT"
    assert cases["revalidation_scaffold_high_risk"]["recommended_action_id"] != "execute_non_solver_revalidation"
    assert cases["summary_acknowledged"]["observed"] == "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED"
    assert cases["unsafe_final_approval_fixture"]["observed"] == "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
    assert all(case["passed"] for case in result["smoke_cases"])


def test_gui_beta_smoke_component_checks_and_safety_flags() -> None:
    result = build_gui_beta_e2e_smoke(ROOT, task_dir=TASK)
    checks = result["component_checks"]
    for key in [
        "workflow_state_model",
        "safe_action_catalog",
        "visual_layout_sections",
        "workflow_timeline",
        "trace_viewer",
        "timeline_interaction",
        "artifact_preview",
        "report_viewer_card",
        "next_step_recommendation",
        "disabled_actions_callback_free",
        "no_generic_executor",
        "unsafe_claim_fixture",
    ]:
        assert checks[key] is True
    assert result["gui_beta_ready"] is True
    assert result["final_evidence_approved"] is False
    assert result["final_verdict_frozen"] is False
    assert result["auto_execute_allowed"] is False


def test_write_gui_beta_smoke_outputs(tmp_path: Path) -> None:
    output = tmp_path / "gui_beta"
    result = write_gui_beta_e2e_smoke_outputs(ROOT, task_dir=TASK, output_dir=output)
    assert result["verdict"] == "GUI_BETA_E2E_SMOKE_REPORT_READY"
    assert (output / "GUI_BETA_E2E_SMOKE_RESULT.json").exists()
    assert (output / "GUI_BETA_E2E_SMOKE_REPORT.md").exists()
    assert (output / "GUI_BETA_CHECKLIST.md").exists()
