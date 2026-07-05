from __future__ import annotations

from abqpilot.acom.supervisor_non_solver_summary_ack_schema import (
    ACK_ACCEPTED,
    ACK_GATE,
    validate_supervisor_non_solver_summary_ack,
)


def test_supervisor_non_solver_summary_ack_schema_accepts_valid_payload():
    valid, errors = validate_supervisor_non_solver_summary_ack(_payload())
    assert valid, errors


def test_supervisor_non_solver_summary_ack_schema_rejects_unknown_status():
    payload = _payload()
    payload["ack_status"] = "NOPE"
    valid, errors = validate_supervisor_non_solver_summary_ack(payload)
    assert not valid
    assert "unknown supervisor non-solver summary ack status" in errors


def test_supervisor_non_solver_summary_ack_schema_rejects_final_flags():
    for field in ["final_evidence_approved", "final_verdict_frozen", "solver_approved", "odb_metrics_approved", "task_final_evidence_ledger_updated"]:
        payload = _payload()
        payload[field] = True
        valid, errors = validate_supervisor_non_solver_summary_ack(payload)
        assert not valid
        assert any(field in error for error in errors)


def _payload() -> dict:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.0I",
        "task_id": "task",
        "task_dir": "task",
        "ack_status": ACK_ACCEPTED,
        "gate_decision": ACK_GATE,
        "summary_result_path": "summary.json",
        "summary_report_path": "summary.md",
        "ledger_json_path": "ledger.json",
        "ledger_md_path": "ledger.md",
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "task_final_evidence_ledger_updated": False,
        "non_solver_summary_ack_ledger_entry_created": True,
        "safety_flags": {"solver_run": False},
        "handoff_path": "handoff.md",
    }
