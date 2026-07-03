from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 4.2"

ALLOWED_REPAIR_TYPES = {
    "step_increment_relaxation",
    "minimum_increment_reduction",
    "maximum_increment_attempts_increase",
    "load_ramp_smoothing",
    "automatic_stabilization_candidate",
    "output_request_only_adjustment",
    "manual_review_required",
    "no_safe_repair_available",
}

FORBIDDEN_REPAIR_TYPES = {
    "material_change",
    "elastic_property_change",
    "plastic_property_change",
    "geometry_change",
    "mesh_change",
    "boundary_condition_change",
    "contact_change",
    "raw_inp_edit",
    "solver_submit",
    "queue_runner_launch",
    "direct_odb_open",
}

FORBIDDEN_PATCH_SCOPE = [
    "material",
    "geometry",
    "mesh",
    "boundary_condition",
    "contact",
    "raw_inp_edit",
    "solver_submit",
    "queue_runner_launch",
    "direct_odb_open",
]

ALLOWED_PATCH_SCOPE = [
    "step_incrementation_controls",
    "load_amplitude_smoothing_if_existing_amplitude_present",
    "output_request_adjustment",
]


def validate_repair_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    recommended = proposal.get("recommended_repair_type")
    secondary = proposal.get("secondary_repair_types", [])
    all_types = [recommended] + list(secondary or [])
    for item in all_types:
        if item in FORBIDDEN_REPAIR_TYPES:
            errors.append(f"forbidden repair type: {item}")
        elif item not in ALLOWED_REPAIR_TYPES:
            errors.append(f"unknown repair type: {item}")
    if proposal.get("requires_human_review") is not True:
        errors.append("requires_human_review must be true")
    if proposal.get("apply_repair_now") is not False:
        errors.append("apply_repair_now must be false")
    if proposal.get("run_solver_now") is not False:
        errors.append("run_solver_now must be false")
    for scope in proposal.get("allowed_patch_scope", []):
        if scope in FORBIDDEN_PATCH_SCOPE:
            errors.append(f"forbidden scope in allowed_patch_scope: {scope}")
    status = "PASS" if not errors else "REPAIR_PROPOSAL_REJECTED_BY_SCHEMA"
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "status": status,
        "valid": not errors,
        "errors": errors,
        "warnings": [],
    }

