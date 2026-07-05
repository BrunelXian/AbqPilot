from __future__ import annotations

from abqpilot.acom.non_solver_evidence_summary_schema import (
    READY_GATE,
    READY_STATUS,
    validate_non_solver_evidence_summary,
    validate_non_solver_ledger,
)


def test_non_solver_ledger_schema_validates_required_fields():
    valid, errors, warnings = validate_non_solver_ledger({"schema_version": "0.1", "ledger_type": "non_solver_evidence", "entries": [_entry()]})
    assert valid
    assert errors == []
    assert warnings == []


def test_non_solver_ledger_blocks_final_evidence_approval():
    entry = _entry()
    entry["final_evidence_approved"] = True
    valid, errors, _warnings = validate_non_solver_ledger({"schema_version": "0.1", "ledger_type": "non_solver_evidence", "entries": [entry]})
    assert not valid
    assert any("final evidence approval" in error for error in errors)


def test_non_solver_summary_schema_rejects_unknown_status():
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.0H",
        "task_id": "task",
        "task_dir": "task",
        "summary_status": "NOPE",
        "gate_decision": READY_GATE,
        "ledger_json_path": "ledger.json",
        "ledger_md_path": "ledger.md",
        "entries_reviewed": 1,
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "task_final_evidence_ledger_updated": False,
        "safety_flags": {},
    }
    valid, errors = validate_non_solver_evidence_summary(payload)
    assert not valid
    assert "unknown non-solver evidence summary status" in errors


def test_non_solver_summary_schema_accepts_ready_payload():
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.0H",
        "task_id": "task",
        "task_dir": "task",
        "summary_status": READY_STATUS,
        "gate_decision": READY_GATE,
        "ledger_json_path": "ledger.json",
        "ledger_md_path": "ledger.md",
        "entries_reviewed": 1,
        "automatic_execution_performed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "task_final_evidence_ledger_updated": False,
        "safety_flags": {"solver_run": False},
        "handoff_path": "handoff.md",
    }
    valid, errors = validate_non_solver_evidence_summary(payload)
    assert valid, errors


def _entry() -> dict:
    return {
        "task_id": "task",
        "source_revalidation_agent": "DocsStatusAgent",
        "source_revalidation_status": "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
        "supervisor_review_status": "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER",
        "ledger_decision": "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER",
        "artifacts_reviewed": [],
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
    }
