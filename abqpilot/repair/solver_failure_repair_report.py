from __future__ import annotations

from typing import Any


def render_solver_failure_repair_summary(proposal: dict[str, Any], validation: dict[str, Any]) -> str:
    lines = [
        "# Stage 4.2 Solver Failure Repair Proposal",
        "",
        f"Status: `{proposal.get('repair_proposal_status')}`",
        f"Diagnosis: `{proposal.get('diagnosis_status')}`",
        f"Failure category: `{proposal.get('failure_category')}`",
        f"Recommended repair type: `{proposal.get('recommended_repair_type')}`",
        f"Secondary repair types: `{', '.join(proposal.get('secondary_repair_types', []))}`",
        f"Requires human review: `{proposal.get('requires_human_review')}`",
        f"Apply repair now: `{proposal.get('apply_repair_now')}`",
        f"Run solver now: `{proposal.get('run_solver_now')}`",
        f"Validation: `{validation.get('status')}`",
        "",
        "## Allowed Patch Scope",
        "",
    ]
    lines.extend(f"- `{item}`" for item in proposal.get("allowed_patch_scope", []))
    lines.extend(["", "## Forbidden Patch Scope", ""])
    lines.extend(f"- `{item}`" for item in proposal.get("forbidden_patch_scope", []))
    lines.extend(["", "## Evidence Summary", ""])
    for key, value in proposal.get("evidence_summary", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "This stage does not apply repairs, mutate INP files, open ODB files, enqueue jobs, or run Abaqus.",
        ]
    )
    return "\n".join(lines) + "\n"

