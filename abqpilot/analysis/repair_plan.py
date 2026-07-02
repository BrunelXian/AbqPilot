from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_PATCH_TYPES = [
    "heat_flux_magnitude_adjustment",
    "step_time_adjustment",
    "output_request_adjustment",
]

FORBIDDEN_PATCH_TYPES = [
    "material_change",
    "geometry_change",
    "mesh_change",
    "boundary_condition_change",
    "solver_submit",
]


def build_repair_plan(evaluation: dict[str, Any], task_id: str | None = None, source_metrics: str | None = None) -> dict[str, Any]:
    verdict = evaluation.get("evaluation_verdict", "INSUFFICIENT_METRICS")
    repair_required = verdict in {"REPAIR_RECOMMENDED", "FAIL_STOP", "INSUFFICIENT_METRICS"}
    if verdict == "PASS":
        next_action = "No automatic repair is recommended. Preserve current audited input and proceed with human review."
        candidate_patch = None
    elif verdict == "INSUFFICIENT_METRICS":
        next_action = "Collect missing metrics through the existing gated ODB metrics extractor before proposing an input patch."
        candidate_patch = {"patch_type": "output_request_adjustment", "description": "Request missing comparison metrics in future guarded runs."}
    elif verdict == "REPAIR_RECOMMENDED":
        next_action = "Prepare a guarded heat-flux magnitude adjustment proposal for human review."
        candidate_patch = {"patch_type": "heat_flux_magnitude_adjustment", "scale_direction": "review_required"}
    else:
        next_action = "Stop automatic progression and require human review of extraction or solver failure evidence."
        candidate_patch = None
    return {
        "schema_version": "0.1",
        "task_id": task_id or evaluation.get("task_id"),
        "source_metrics": source_metrics or evaluation.get("source_metrics"),
        "evaluation_verdict": verdict,
        "repair_required": repair_required,
        "recommended_next_action": next_action,
        "allowed_patch_types": ALLOWED_PATCH_TYPES,
        "forbidden_patch_types": FORBIDDEN_PATCH_TYPES,
        "candidate_patch": candidate_patch,
        "requires_human_review": True,
        "mutated_inp": False,
        "submitted_solver": False,
    }


def render_repair_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Deterministic Repair Plan",
        "",
        f"Evaluation verdict: `{plan.get('evaluation_verdict')}`",
        f"Repair required: `{plan.get('repair_required')}`",
        f"Recommended next action: {plan.get('recommended_next_action')}",
        "",
        "## Allowed Patch Types",
        "",
    ]
    lines.extend(f"- `{item}`" for item in plan.get("allowed_patch_types", []))
    lines.extend(["", "## Forbidden Patch Types", ""])
    lines.extend(f"- `{item}`" for item in plan.get("forbidden_patch_types", []))
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- No INP was mutated.",
            "- No solver job was submitted.",
            "- Human review is required before any future guarded patch.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_repair_plan(out_dir: str | Path, evaluation: dict[str, Any], task_id: str | None = None) -> dict[str, str]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    plan = build_repair_plan(evaluation, task_id=task_id)
    evaluation_path = target / "evaluation.json"
    plan_path = target / "repair_plan.json"
    markdown_path = target / "repair_plan.md"
    evaluation_path.write_text(json.dumps(evaluation, indent=2, ensure_ascii=False), encoding="utf-8")
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(render_repair_plan_markdown(plan), encoding="utf-8")
    return {
        "evaluation_json": str(evaluation_path),
        "repair_plan_json": str(plan_path),
        "repair_plan_md": str(markdown_path),
    }
