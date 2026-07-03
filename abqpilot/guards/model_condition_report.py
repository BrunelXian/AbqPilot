from __future__ import annotations

from typing import Any


def render_mcp_report(result: dict[str, Any]) -> str:
    findings = result.get("condition_findings", [])
    lines = [
        "# Stage 4.5 Model Condition Preservation Guard",
        "",
        f"Guard status: `{result.get('guard_status')}`",
        f"Eligible for solver: `{result.get('eligible_for_solver')}`",
        f"Target patch isolation: `{result.get('target_patch_isolation', {}).get('status')}`",
        "",
        "## Findings",
        "",
    ]
    for item in findings:
        lines.extend(
            [
                f"- `{item.get('subcategory') or item.get('category')}` / `{item.get('condition_name')}`: `{item.get('status')}`",
                f"  - Code: `{item.get('finding_code')}`",
                f"  - Severity: `{item.get('severity')}`",
                f"  - Recommended action: {item.get('recommended_action')}",
            ]
        )
    lines.extend(
        [
            "",
            "MCPGuard complements StaticValidator, DiffGuard, and PhysicsGuard. It validates that non-target original model conditions are preserved across export, patching, and solver-run copies.",
        ]
    )
    return "\n".join(lines) + "\n"
