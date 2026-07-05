from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def build_gui_beta_readiness_result(
    *,
    project_root: str | Path,
    smoke_cases: list[dict[str, Any]],
    component_checks: dict[str, bool],
    tests_baseline_before: str = "699 passed",
    tests_result_after: str | None = None,
    docs_updated: bool = True,
) -> dict[str, Any]:
    safety_checks = {
        "disabled_actions_check": bool(component_checks.get("disabled_actions_callback_free")),
        "safety_boundary_check": bool(component_checks.get("safety_copy_present")),
        "final_evidence_locked_check": bool(component_checks.get("final_evidence_locked")),
        "codex_external_only_check": bool(component_checks.get("codex_external_only")),
        "solver_odb_metrics_disabled_check": bool(component_checks.get("solver_odb_metrics_disabled")),
        "no_auto_execution_check": bool(component_checks.get("no_auto_execution")),
        "no_generic_executor_check": bool(component_checks.get("no_generic_executor")),
        "no_final_approval_check": bool(component_checks.get("no_final_approval")),
        "unsafe_claim_fixture_check": bool(component_checks.get("unsafe_claim_fixture")),
    }
    all_cases_pass = all(case.get("passed") is True for case in smoke_cases)
    all_components_pass = all(component_checks.values()) if component_checks else False
    all_safety_pass = all(safety_checks.values())
    ready = all_cases_pass and all_components_pass and all_safety_pass
    return {
        "schema_version": "0.1",
        "stage_id": "STAGE5_1F",
        "stage": "Stage 5.1F",
        "verdict": "PASS_ABQPILOT_V2_STAGE5_1F_GUI_E2E_SAFE_WORKFLOW_BETA_READY" if ready else "GUI_BETA_E2E_SMOKE_BLOCKED",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(Path(project_root)),
        "tests_baseline_before": tests_baseline_before,
        "tests_result_after": tests_result_after,
        "smoke_cases": smoke_cases,
        "component_checks": component_checks,
        **safety_checks,
        "docs_updated": docs_updated,
        "known_limitations": [
            "GUI beta readiness is non-final and non-solver only.",
            "The smoke validates view models and safety boundaries; it does not execute workflow actions.",
            "Future solver, ODB, metrics, final evidence, or Codex automation requires explicit later stages.",
        ],
        "gui_beta_ready": ready,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "codex_cli_called": False,
        "queue_runner_launched": False,
        "auto_execute_allowed": False,
    }
