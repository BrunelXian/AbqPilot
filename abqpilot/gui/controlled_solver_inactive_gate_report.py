from __future__ import annotations

from typing import Any


def render_controlled_solver_inactive_gate_report(draft: dict[str, Any], validation: dict[str, Any]) -> str:
    lines = [
        "# Controlled Solver Inactive Human Gate Draft",
        "",
        "Inactive draft only; not an approval.",
        "No active gate record is created in Stage 5.2C.",
        "No Abaqus solver command is executed.",
        "No solver request file is created.",
        "Future active human approval gate creation must be a separate explicit stage.",
        "Future solver execution must be a later separate explicit stage.",
        "Final evidence remains locked.",
        "ODB and metrics remain disabled.",
        "Queue mutation remains disabled.",
        "",
        "## Draft Status",
        "",
        f"- draft_type: `{draft['draft_type']}`",
        f"- gate_type: `{draft['gate_type']}`",
        f"- draft_status: `{draft['draft_status']}`",
        f"- validation_status: `{validation['validation_status']}`",
        f"- approval_status: `{draft['approval_status']}`",
        f"- gate_decision: `{draft['gate_decision']}`",
        f"- execution_status: `{draft['execution_status']}`",
        f"- active_gate_record_created: `{draft['active_gate_record_created']}`",
        f"- solver_request_created: `{draft['solver_request_created']}`",
        f"- final_evidence_approved: `{draft['final_evidence_approved']}`",
        f"- final_verdict_frozen: `{draft['final_verdict_frozen']}`",
        "",
        "## Expected Future Active Gate Shape",
        "",
        "This shape is expected future data only. It is not written as an active task gate record.",
        "",
    ]
    for key, value in draft["expected_future_active_gate_shape"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Expected Future Solver Execution Handoff Shape", ""])
    lines.append("This shape is expected future data only. It is not written as an active executable handoff.")
    lines.append("")
    for key, value in draft["expected_future_solver_execution_handoff_shape"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            draft["safety_boundary"],
            "",
            "## Claim Boundary",
            "",
            "This inactive draft is not active approval, solver execution, ODB acceptance, metrics acceptance, final evidence approval, or final verdict freeze.",
            "",
            f"Verdict: `{draft.get('verdict', 'CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_REPORT_READY')}`",
        ]
    )
    return "\n".join(lines) + "\n"
