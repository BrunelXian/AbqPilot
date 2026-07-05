from __future__ import annotations

from typing import Any

from abqpilot.gui.high_risk_gate_catalog import get_high_risk_action


SAFETY_BOUNDARY = (
    "Stage 5.2A is preview-only. It does not run solver, open ODB, queue jobs, call Codex CLI, "
    "auto-schedule agents, approve gates, approve final evidence, freeze verdicts, or mutate "
    "TASK_FINAL_EVIDENCE_LEDGER.md."
)


def build_high_risk_gate_ux(action_id: str) -> dict[str, Any]:
    action = get_high_risk_action(action_id)
    prerequisites = list(action["required_prerequisites"])
    return {
        "action_id": action["action_id"],
        "display_name": action["display_name"],
        "risk_level": action["risk_level"],
        "current_allowed": False,
        "executable": False,
        "preview_only": True,
        "approval_status": "NOT_APPROVED",
        "execution_status": "NOT_EXECUTABLE",
        "human_gate_required": True,
        "future_stage_required": True,
        "disabled_reason": action["disabled_reason"],
        "risk_summary": action["risk_summary"],
        "prerequisite_checklist": prerequisites,
        "missing_prerequisites": [item["prerequisite_id"] for item in prerequisites],
        "required_evidence_inputs": action["required_evidence_inputs"],
        "expected_future_outputs": action["expected_future_outputs"],
        "warning_copy": action["user_warning_copy"],
        "confirmation_copy_preview": action["required_confirmation_copy"],
        "forbidden_actions": action["forbidden_without_gate"],
        "final_evidence_effect": action["final_evidence_effect"],
        "safety_boundary": SAFETY_BOUNDARY,
        "user_instruction": "Preview gate requirements only. Do not approve, execute, or manually bypass the future gate.",
        "recommended_future_stage": f"Future explicit human gate for {action['action_id']}",
        "read_only_notice": "Preview only; not an approval",
        "no_execution_notice": "This GUI does not execute the high-risk action",
        "required_copy": [
            "Preview only; not an approval",
            "This GUI does not execute the high-risk action",
            "Human gate required in a future explicit stage",
            "Final evidence remains locked",
            "No solver / ODB / queue / Codex / final freeze is enabled in Stage 5.2A",
        ],
        "real_gate_created": False,
        "auto_execute_allowed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "queue_runner_launched": False,
        "codex_cli_called": False,
        "task_final_evidence_ledger_updated": False,
    }


def build_all_high_risk_gate_ux_previews(action_ids: list[str]) -> list[dict[str, Any]]:
    return [build_high_risk_gate_ux(action_id) for action_id in action_ids]
