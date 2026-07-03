from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 4.3"
PATCH_TYPE = "dflux_deactivation_reset"
INSERTED_KEYWORD = "*Dflux, OP=NEW"
MCP_SUBCHECK = "MCPGuard.load_lifecycle.body_heat_flux_dflux_bf"
FORBIDDEN_SCOPES = [
    "material",
    "geometry",
    "mesh",
    "boundary_condition",
    "contact",
    "raw_unbounded_inp_edit",
    "solver_submit",
    "queue_runner_launch",
    "direct_odb_open",
]


def build_patch_plan(
    source_inp: str,
    candidate_preview_inp: str,
    scan_step: str,
    cooling_step: str,
    load_name: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "patch_type": PATCH_TYPE,
        "mcp_guard_subcheck": MCP_SUBCHECK,
        "source_inp": source_inp,
        "candidate_preview_inp": candidate_preview_inp,
        "scan_step": scan_step,
        "cooling_step": cooling_step,
        "load_name": load_name,
        "inserted_keyword": INSERTED_KEYWORD,
        "expected_effect": "reset/remove propagated DFLUX loads at the cooling step start",
        "apply_repair_now": False,
        "run_solver_now": False,
        "requires_human_review": True,
        "forbidden_scopes": FORBIDDEN_SCOPES,
    }


def validate_patch_plan(plan: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if plan.get("patch_type") != PATCH_TYPE:
        errors.append("patch_type must be dflux_deactivation_reset")
    if plan.get("inserted_keyword") != INSERTED_KEYWORD:
        errors.append("inserted_keyword must be *Dflux, OP=NEW")
    if plan.get("apply_repair_now") is not False:
        errors.append("apply_repair_now must be false")
    if plan.get("run_solver_now") is not False:
        errors.append("run_solver_now must be false")
    if plan.get("requires_human_review") is not True:
        errors.append("requires_human_review must be true")
    forbidden = set(plan.get("forbidden_scopes", []))
    missing = [scope for scope in FORBIDDEN_SCOPES if scope not in forbidden]
    if missing:
        errors.append(f"missing forbidden scopes: {missing}")
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "valid": not errors,
        "status": "PASS" if not errors else "DFLUX_LIFECYCLE_PATCH_PLAN_INVALID",
        "errors": errors,
    }
