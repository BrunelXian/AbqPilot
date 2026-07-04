from __future__ import annotations

from abqpilot.acom.non_solver_revalidation_schema import (
    HIGH_RISK_BLOCKED_AGENTS,
    SUPPORTED_NON_SOLVER_AGENTS,
    validate_non_solver_revalidation_result,
)


def test_supported_and_blocked_agent_sets_are_disjoint():
    assert "DocsStatusAgent" in SUPPORTED_NON_SOLVER_AGENTS
    assert "GuardAgent" in HIGH_RISK_BLOCKED_AGENTS
    assert not (SUPPORTED_NON_SOLVER_AGENTS & HIGH_RISK_BLOCKED_AGENTS)


def test_schema_rejects_approved_gate():
    payload = _payload()
    payload["gate_decision"] = "APPROVED"
    valid, errors = validate_non_solver_revalidation_result(payload)
    assert not valid
    assert any("APPROVED" in error for error in errors)


def test_schema_requires_no_final_evidence_approval():
    payload = _payload()
    payload["final_evidence_approved"] = True
    valid, errors = validate_non_solver_revalidation_result(payload)
    assert not valid
    assert any("final_evidence_approved" in error for error in errors)


def _payload():
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.0F",
        "task_id": "task",
        "task_dir": "task",
        "revalidation_dir": "task/revalidation/DocsStatusAgent_test",
        "downstream_agent": "DocsStatusAgent",
        "result_status": "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
        "checks": [],
        "pass_items": [],
        "warning_items": [],
        "fail_items": [],
        "gate_decision": "PENDING_SUPERVISOR_REVIEW",
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "codex_summary_is_final_evidence": False,
        "safety_flags": {
            "codex_cli_called": False,
            "solver_run": False,
            "queue_runner_launched": False,
            "odb_opened": False,
            "source_cae_mutated": False,
            "source_inp_mutated": False,
            "env_read": False,
            "shell_true_used": False,
            "automatic_scheduling_added": False,
            "high_risk_agent_executed": False,
        },
    }
