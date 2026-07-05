from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from abqpilot.gui.artifact_preview import build_artifact_preview
from abqpilot.gui.beta_checklist import build_gui_beta_checklist, render_gui_beta_checklist_markdown
from abqpilot.gui.beta_readiness import build_gui_beta_readiness_result
from abqpilot.gui.beta_report import render_gui_beta_smoke_report
from abqpilot.gui.layout_sections import build_layout_sections
from abqpilot.gui.next_step_recommender import build_next_step_recommendation
from abqpilot.gui.recommendation_cards import build_next_step_recommendation_card
from abqpilot.gui.recommendation_rules import recommendation_for_workflow_state
from abqpilot.gui.report_viewer import build_report_viewer_card
from abqpilot.gui.safe_action_catalog import get_disabled_high_risk_actions, get_safe_action_catalog
from abqpilot.gui.timeline_interaction import select_timeline_step
from abqpilot.gui.trace_viewer import build_trace_viewer
from abqpilot.gui.workflow_state import inspect_gui_workflow_state


def build_gui_beta_e2e_smoke(
    project_root: str | Path,
    *,
    task_dir: str | Path | None = None,
    tests_result_after: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    selected_task = Path(task_dir) if task_dir is not None else root / "runs" / "tasks" / "stage5_0f_non_solver_revalidation_smoke"
    smoke_cases = _synthetic_state_cases()
    smoke_cases.extend(_live_task_cases(selected_task))
    component_checks = _component_checks(root, selected_task)
    return build_gui_beta_readiness_result(
        project_root=root,
        smoke_cases=smoke_cases,
        component_checks=component_checks,
        tests_result_after=tests_result_after,
    )


def write_gui_beta_e2e_smoke_outputs(
    project_root: str | Path,
    *,
    task_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    tests_result_after: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    output = Path(output_dir) if output_dir is not None else root / "gui_beta"
    output.mkdir(parents=True, exist_ok=True)
    result = build_gui_beta_e2e_smoke(root, task_dir=task_dir, tests_result_after=tests_result_after)
    checklist = build_gui_beta_checklist(result.get("component_checks", {}))
    result_path = output / "GUI_BETA_E2E_SMOKE_RESULT.json"
    report_path = output / "GUI_BETA_E2E_SMOKE_REPORT.md"
    checklist_path = output / "GUI_BETA_CHECKLIST.md"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_gui_beta_smoke_report(result), encoding="utf-8")
    checklist_path.write_text(render_gui_beta_checklist_markdown(checklist), encoding="utf-8")
    return {
        "command": "report-gui-beta-smoke",
        "verdict": "GUI_BETA_E2E_SMOKE_REPORT_READY" if result.get("gui_beta_ready") else "GUI_BETA_E2E_SMOKE_BLOCKED",
        "success": bool(result.get("gui_beta_ready")),
        "result": result,
        "output_paths": {
            "result_json": str(result_path),
            "report_md": str(report_path),
            "checklist_md": str(checklist_path),
        },
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "auto_execute_allowed": False,
    }


def _synthetic_state_cases() -> list[dict[str, Any]]:
    cases = [
        ("no_task", "GUI_STATE_NO_TASK_SELECTED", None, "NEXT_STEP_NO_TASK_SELECTED"),
        ("fresh_scaffold", "GUI_STATE_TASK_SCAFFOLDED", None, "NEXT_STEP_READY"),
        ("acom_handoff_ready", "GUI_STATE_ACOM_HANDOFF_READY", None, "NEXT_STEP_WAITING_FOR_EXTERNAL_CODEX_RESULT"),
        ("acom_result_pending_intake", "GUI_STATE_ACOM_RESULT_PENDING_INTAKE", None, "NEXT_STEP_READY"),
        ("acom_result_accepted_pending_revalidation", "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION", None, "NEXT_STEP_PENDING_REVALIDATION"),
        ("revalidation_scaffold_low_risk", "GUI_STATE_REVALIDATION_SCAFFOLD_READY", "DocsStatusAgent", "NEXT_STEP_READY"),
        ("revalidation_scaffold_high_risk", "GUI_STATE_REVALIDATION_SCAFFOLD_READY", "GuardAgent", "NEXT_STEP_REVIEW_REQUIRED"),
        ("non_solver_revalidation_pending_supervisor", "GUI_STATE_NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR", None, "NEXT_STEP_PENDING_SUPERVISOR_REVIEW"),
        ("supervisor_review_accepted", "GUI_STATE_SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER", None, "NEXT_STEP_READY"),
        ("summary_ready_pending_ack", "GUI_STATE_NON_SOLVER_SUMMARY_READY_PENDING_ACK", None, "NEXT_STEP_PENDING_SUMMARY_ACK"),
        ("summary_acknowledged", "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED", None, "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED"),
    ]
    results: list[dict[str, Any]] = []
    for case_id, state, agent, expected in cases:
        recommendation = recommendation_for_workflow_state(_state_payload(state), downstream_agent=agent)
        observed = recommendation["recommendation_status"]
        passed = observed == expected and recommendation["auto_execute_allowed"] is False
        if case_id == "acom_handoff_ready":
            passed = passed and recommendation["codex_execution_allowed"] is False and any("Codex" in item for item in recommendation["warnings"])
        if case_id == "revalidation_scaffold_high_risk":
            passed = passed and recommendation["recommended_action_id"] != "execute_non_solver_revalidation"
        if case_id == "summary_acknowledged":
            passed = passed and any("Final evidence remains locked" in item for item in recommendation["warnings"])
        results.append(
            {
                "case_id": case_id,
                "expected": expected,
                "observed": observed,
                "passed": passed,
                "recommended_action_id": recommendation.get("recommended_action_id"),
                "final_evidence_effect": recommendation.get("final_evidence_effect"),
                "auto_execute_allowed": recommendation.get("auto_execute_allowed"),
            }
        )
    results.append(_unsafe_claim_fixture_case())
    return results


def _live_task_cases(task: Path) -> list[dict[str, Any]]:
    recommendation = build_next_step_recommendation(task)
    trace = build_trace_viewer(task)
    summary_json = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"
    summary_md = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md"
    preview_json = build_artifact_preview(summary_json)
    preview_md = build_artifact_preview(summary_md)
    return [
        {
            "case_id": "live_stage5_0i_summary_acknowledged",
            "expected": "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED",
            "observed": recommendation.get("recommendation_status"),
            "passed": recommendation.get("recommendation_status") == "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED"
            and trace.get("viewer_state") == "TRACE_VIEWER_READY"
            and preview_json.get("parse_status") == "ARTIFACT_PREVIEW_READY"
            and preview_md.get("parse_status") == "ARTIFACT_PREVIEW_READY"
            and recommendation.get("auto_execute_allowed") is False,
            "trace_viewer_state": trace.get("viewer_state"),
            "json_preview": preview_json.get("parse_status"),
            "markdown_preview": preview_md.get("parse_status"),
        }
    ]


def _component_checks(root: Path, task: Path) -> dict[str, bool]:
    workflow = inspect_gui_workflow_state(task)
    catalog = get_safe_action_catalog()
    disabled = get_disabled_high_risk_actions()
    layout = build_layout_sections(task, root)
    trace = build_trace_viewer(task)
    selected = select_timeline_step(task, "supervisor_ack")
    summary_md = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md"
    preview = build_artifact_preview(summary_md)
    report_card = build_report_viewer_card(summary_md)
    recommendation = build_next_step_recommendation(task)
    card = build_next_step_recommendation_card(task)
    return {
        "workflow_state_model": bool(workflow.get("state")),
        "safe_action_catalog": bool(catalog),
        "visual_layout_sections": bool(layout.get("workflow_timeline")),
        "workflow_timeline": len(layout.get("workflow_timeline", [])) == 8,
        "trace_viewer": trace.get("viewer_state") in {"TRACE_VIEWER_READY", "TRACE_VIEWER_NO_TRACE_RECORDS", "TRACE_VIEWER_READY_WITH_MISSING_FILES"},
        "timeline_interaction": selected.get("read_only") is True and selected.get("action_allowed") is False,
        "artifact_preview": preview.get("read_only") is True,
        "report_viewer_card": report_card.get("read_only") is True and report_card.get("action_allowed") is False,
        "next_step_recommendation": recommendation.get("auto_execute_allowed") is False,
        "disabled_actions_callback_free": bool(disabled) and all(item.get("backend_method") is None for item in disabled),
        "safety_copy_present": "Recommendation only" in " ".join(card.get("copy", []) + card.get("safety_notes", [])),
        "final_evidence_locked": recommendation.get("final_evidence_approved") is False and recommendation.get("final_verdict_frozen") is False,
        "codex_external_only": recommendation.get("codex_execution_allowed") is False,
        "solver_odb_metrics_disabled": recommendation.get("solver_approved") is False and recommendation.get("odb_approved") is False and recommendation.get("metrics_approved") is False,
        "no_auto_execution": recommendation.get("auto_execute_allowed") is False,
        "no_generic_executor": card.get("action_allowed") is False,
        "no_final_approval": recommendation.get("final_evidence_effect") not in {"FINAL_EVIDENCE_APPROVAL", "FINAL_VERDICT_FREEZE"},
        "unsafe_claim_fixture": _unsafe_claim_fixture_case()["passed"],
    }


def _unsafe_claim_fixture_case() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="abqpilot_gui_beta_unsafe_") as temp_dir:
        path = Path(temp_dir) / "unsafe_claim.json"
        path.write_text('{"final_evidence_approved": true}', encoding="utf-8")
        preview = build_artifact_preview(path)
        passed = preview.get("parse_status") == "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
        return {
            "case_id": "unsafe_final_approval_fixture",
            "expected": "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM",
            "observed": preview.get("parse_status"),
            "passed": passed,
            "mutation_performed": False,
        }


def _state_payload(state: str) -> dict[str, Any]:
    return {
        "state": state,
        "current_stage_label": state,
        "latest_status": None,
        "gate_records": {"latest_decision": None},
        "warning_messages": [],
    }
