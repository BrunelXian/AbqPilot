from __future__ import annotations

from typing import Any


def render_real_gate_creation_report(gate: dict[str, Any], validation: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Controlled Solver Real Human Gate Without Execution",
            "",
            "Stage 5.2F creates a real human approval gate only for the dedicated smoke task.",
            "",
            f"Task ID: {gate.get('task_id')}",
            f"Gate ID: {gate.get('gate_id')}",
            f"Decision: {gate.get('decision')}",
            f"Solver approved: {gate.get('solver_approved')}",
            f"Solver execution allowed: {gate.get('solver_execution_allowed')}",
            f"Solver request created: {gate.get('solver_request_created')}",
            "",
            "Human approval gate creation does not execute solver.",
            "No solver request files are created.",
            "No Abaqus solver command is executed.",
            "No ODB/metrics/final evidence authority is granted.",
            "Solver execution remains a future separate explicit stage.",
            "`TASK_FINAL_EVIDENCE_LEDGER.md` remains untouched.",
            "",
            f"Validation: {validation.get('validation_status')}",
        ]
    )


def render_real_gate_validation_report(validation: dict[str, Any]) -> str:
    lines = ["# Controlled Solver Real Gate Validation Report", ""]
    for key, value in validation.get("checks", {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def render_no_execution_audit(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Controlled Solver Real Gate No-Execution Audit",
            "",
            f"solver_execution_allowed: {result.get('solver_execution_allowed')}",
            f"solver_request_created: {result.get('solver_request_created')}",
            f"solver_run: {result.get('solver_run')}",
            f"queue_runner_launched: {result.get('queue_runner_launched')}",
            f"odb_opened: {result.get('odb_opened')}",
            f"odb_metrics_approved: {result.get('odb_metrics_approved')}",
            f"final_evidence_approved: {result.get('final_evidence_approved')}",
            f"final_verdict_frozen: {result.get('final_verdict_frozen')}",
            f"task_final_evidence_ledger_updated: {result.get('task_final_evidence_ledger_updated')}",
            f"no_solver_request_files_found: {result.get('no_solver_request_files_found')}",
            f"no_execution_handoff_found: {result.get('no_execution_handoff_found')}",
            f"no_queue_files_found: {result.get('no_queue_files_found')}",
            f"no_odb_files_found: {result.get('no_odb_files_found')}",
            "",
        ]
    )
