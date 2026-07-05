from __future__ import annotations

from typing import Any


CHECKLIST_ITEMS = (
    "Stage 5.1A workflow state model",
    "Stage 5.1A safe action catalog",
    "Stage 5.1B visual layout sections",
    "Stage 5.1B workflow timeline",
    "Stage 5.1C trace viewer",
    "Stage 5.1C timeline interaction",
    "Stage 5.1D artifact preview",
    "Stage 5.1D report viewer card",
    "Stage 5.1E next-step recommendation",
    "Disabled high-risk action visibility",
    "Final evidence locked boundary",
    "Codex external/manual boundary",
    "Solver / ODB / metrics disabled boundary",
    "Unsafe final-approval claim detection",
)


def build_gui_beta_checklist(component_checks: dict[str, bool] | None = None) -> dict[str, Any]:
    component_checks = component_checks or {}
    items = [
        {
            "item": item,
            "status": "PASS" if component_checks.get(_key(item), True) else "FAIL",
            "claim_boundary": "GUI beta readiness only; not final evidence readiness.",
        }
        for item in CHECKLIST_ITEMS
    ]
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.1F",
        "checklist_name": "GUI Beta Safe Workflow Checklist",
        "items": items,
        "all_passed": all(item["status"] == "PASS" for item in items),
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }


def render_gui_beta_checklist_markdown(checklist: dict[str, Any]) -> str:
    lines = [
        "# GUI Beta Checklist",
        "",
        "This checklist is a non-final GUI beta readiness record.",
        "It is not final evidence approval and does not freeze verdict.",
        "",
        "| Item | Status | Boundary |",
        "| --- | --- | --- |",
    ]
    for item in checklist.get("items", []):
        lines.append(f"| {item['item']} | {item['status']} | {item['claim_boundary']} |")
    return "\n".join(lines) + "\n"


def _key(value: str) -> str:
    return value.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
