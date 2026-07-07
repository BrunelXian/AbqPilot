from __future__ import annotations

from typing import Any


def render_active_gate_design_report(gate: dict[str, Any], validation: dict[str, Any], handoff: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Controlled Solver Active Human Gate Record Design",
            "",
            "## Purpose",
            "Stage 5.2D defines active controlled solver human gate record design only.",
            "",
            "## Safety Boundary",
            "Active gate record design only. No real project gate is written in Stage 5.2D.",
            "Human approval does not execute solver.",
            "Future solver execution must consume the active gate in a later explicit stage.",
            "No Abaqus solver command is executed.",
            "No solver request file is created.",
            "Final evidence remains locked.",
            "ODB and metrics remain disabled.",
            "Queue mutation remains disabled.",
            "",
            "## Schema Summary",
            f"Gate type: {gate.get('gate_type')}",
            f"Decision: {gate.get('decision')}",
            f"Approval status: {gate.get('approval_status')}",
            f"Solver approved in design object: {gate.get('solver_approved')}",
            f"Solver execution allowed: {gate.get('solver_execution_allowed')}",
            f"Real project gate written: {gate.get('real_project_gate_written')}",
            f"Writer enabled: {gate.get('writer_enabled')}",
            "",
            "## Validation",
            f"Validation status: {validation.get('validation_status')}",
            "",
            "## Token Consumption",
            "Token consumption is modeled as audit data only in Stage 5.2D. It does not execute solver and does not approve ODB, metrics, final evidence, or final verdict.",
            "",
            "## Candidate Hash Binding",
            f"Candidate path: {gate.get('candidate_artifact_path')}",
            f"Candidate hash algorithm: {gate.get('candidate_artifact_hash_algorithm')}",
            f"Candidate hash present: {bool(gate.get('candidate_artifact_hash'))}",
            "",
            "## Future Execution Handoff Shape",
            f"Handoff type: {handoff.get('handoff_type')}",
            f"To agent: {handoff.get('to_agent')}",
            f"Solver auto start: {handoff.get('solver_auto_start')}",
            "",
            "## Claim Boundary",
            "This report is a non-final design/specification record. It is not solver readiness, not ODB readiness, not metrics readiness, and not final evidence approval.",
        ]
    )


def render_active_gate_validation_rules() -> str:
    rules = [
        "doc_type must be gate_decision.",
        "gate_type must be CONTROLLED_SOLVER_RUN.",
        "decision and approval_status must be APPROVED_BY_HUMAN.",
        "human approval token must be valid, consumed, one-time use, and non-reusable.",
        "solver_approved may be true only inside the schema/design object.",
        "solver_execution_allowed must be false.",
        "solver_request_created, solver_run, queue_runner_launched, and odb_opened must be false.",
        "ODB metrics approval, final evidence approval, final verdict freeze, and task final ledger updates must be false.",
        "downstream execution auto-start must be false.",
    ]
    return "# Controlled Solver Active Gate Validation Rules\n\n" + "\n".join(f"- {rule}" for rule in rules) + "\n"


def render_token_consumption_rules() -> str:
    rules = [
        "Token must be valid before consumption.",
        "Token must be one-time use.",
        "Token must bind to task_id.",
        "Token must bind to candidate artifact hash.",
        "Token must verify exact approval phrase.",
        "All acknowledgement flags must be true.",
        "Consumed token must not be reused.",
        "Token consumption does not execute solver.",
        "Token consumption does not approve ODB, metrics, final evidence, or final verdict.",
    ]
    return "# Controlled Solver Token Consumption Rules\n\n" + "\n".join(f"- {rule}" for rule in rules) + "\n"


def render_candidate_hash_binding() -> str:
    return "\n".join(
        [
            "# Controlled Solver Candidate Hash Binding",
            "",
            "- SHA256 is the supported algorithm.",
            "- Candidate paths are read as bytes only when allowed.",
            "- `.env`, ODB files, queue.json, live_status.json, runtime/reports, source sanity-base CAE, and source sanity-base INP are forbidden.",
            "- Hash binding does not execute solver and does not create a solver request.",
            "",
        ]
    )


def render_writer_policy() -> str:
    return "\n".join(
        [
            "# Controlled Solver Active Gate Writer Policy",
            "",
            "ACTIVE_GATE_WRITER_DISABLED_IN_STAGE_5_2D",
            "",
            "- writer_enabled=false",
            "- No real active gate is written under real task `gates/`.",
            "- No active execution handoff is written under real task `handoffs/`.",
            "- No solver request file is created.",
            "- Future explicit stage must enable and revalidate writer behavior.",
            "",
        ]
    )
