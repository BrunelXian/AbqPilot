from __future__ import annotations

from abqpilot.acom.revalidation_schema import validate_revalidation_scaffold


def test_revalidation_schema_validates_payload():
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.0E",
        "task_id": "task",
        "status": "REVALIDATION_SCAFFOLD_READY",
        "downstream_agent": "GuardAgent",
        "revalidation_id": "id",
        "automatic_execution_performed": False,
        "codex_summary_is_final_evidence": False,
        "accepted_as_final_evidence": False,
        "gate_decision": "PENDING_REVALIDATION",
        "package_dir": "pkg",
        "profile": {},
    }
    valid, errors = validate_revalidation_scaffold(payload)
    assert valid, errors


def test_revalidation_schema_rejects_auto_execution():
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.0E",
        "task_id": "task",
        "status": "REVALIDATION_SCAFFOLD_READY",
        "downstream_agent": "GuardAgent",
        "revalidation_id": "id",
        "automatic_execution_performed": True,
        "codex_summary_is_final_evidence": False,
        "accepted_as_final_evidence": False,
        "gate_decision": "PENDING_REVALIDATION",
        "package_dir": "pkg",
        "profile": {},
    }
    valid, errors = validate_revalidation_scaffold(payload)
    assert not valid
    assert any("automatic_execution_performed" in error for error in errors)
