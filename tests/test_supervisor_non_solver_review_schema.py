from __future__ import annotations

from abqpilot.acom.supervisor_non_solver_review_schema import validate_supervisor_non_solver_review


def test_supervisor_schema_rejects_final_evidence_approval():
    payload = _payload()
    payload["final_evidence_approved"] = True
    valid, errors = validate_supervisor_non_solver_review(payload)
    assert not valid
    assert any("final_evidence_approved" in error for error in errors)


def test_supervisor_schema_rejects_approved_gate_decision():
    payload = _payload()
    payload["gate_decision"] = "APPROVED"
    valid, errors = validate_supervisor_non_solver_review(payload)
    assert not valid
    assert any("APPROVED" in error for error in errors)


def _payload():
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.0G",
        "task_id": "task",
        "task_dir": "task",
        "review_status": "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER",
        "reviewed_agent": "DocsStatusAgent",
        "reviewed_status": "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
        "gate_decision": "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER",
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "non_solver_ledger_entry_created": True,
        "checks": [],
        "pass_items": [],
        "warning_items": [],
        "fail_items": [],
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
