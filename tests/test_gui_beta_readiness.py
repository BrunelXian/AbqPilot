from pathlib import Path

from abqpilot.gui.beta_readiness import build_gui_beta_readiness_result


def test_gui_beta_readiness_true_only_when_checks_pass(tmp_path: Path) -> None:
    smoke_cases = [{"case_id": "case", "passed": True}]
    checks = {
        "disabled_actions_callback_free": True,
        "safety_copy_present": True,
        "final_evidence_locked": True,
        "codex_external_only": True,
        "solver_odb_metrics_disabled": True,
        "no_auto_execution": True,
        "no_generic_executor": True,
        "no_final_approval": True,
        "unsafe_claim_fixture": True,
    }
    result = build_gui_beta_readiness_result(project_root=tmp_path, smoke_cases=smoke_cases, component_checks=checks)
    assert result["gui_beta_ready"] is True
    assert result["final_evidence_approved"] is False
    assert result["final_verdict_frozen"] is False
    assert result["solver_approved"] is False
    assert result["odb_metrics_approved"] is False
    assert result["codex_cli_called"] is False
    assert result["queue_runner_launched"] is False
    assert result["auto_execute_allowed"] is False


def test_gui_beta_readiness_blocks_when_case_fails(tmp_path: Path) -> None:
    checks = {key: True for key in ["disabled_actions_callback_free", "safety_copy_present", "final_evidence_locked", "codex_external_only", "solver_odb_metrics_disabled", "no_auto_execution", "no_generic_executor", "no_final_approval", "unsafe_claim_fixture"]}
    result = build_gui_beta_readiness_result(project_root=tmp_path, smoke_cases=[{"case_id": "case", "passed": False}], component_checks=checks)
    assert result["gui_beta_ready"] is False
