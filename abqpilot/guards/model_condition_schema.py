from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 4.5"
GUARD_NAME = "Model Condition Preservation Guard"
GUARD_SHORT_NAME = "MCPGuard"

MCP_PASS = "MCP_PASS"
MCP_FAIL_CONDITION_LOSS = "MCP_FAIL_CONDITION_LOSS"
MCP_FAIL_UNAUTHORIZED_CONDITION_CHANGE = "MCP_FAIL_UNAUTHORIZED_CONDITION_CHANGE"
MCP_REVIEW_REQUIRED = "MCP_REVIEW_REQUIRED"
MCP_BLOCKED_MISSING_SOURCE_INTENT = "MCP_BLOCKED_MISSING_SOURCE_INTENT"
MCP_BLOCKED_MISSING_CANDIDATE = "MCP_BLOCKED_MISSING_CANDIDATE"
MCP_BLOCKED_PARSE_ERROR = "MCP_BLOCKED_PARSE_ERROR"

VALID_GUARD_STATUSES = {
    MCP_PASS,
    MCP_FAIL_CONDITION_LOSS,
    MCP_FAIL_UNAUTHORIZED_CONDITION_CHANGE,
    MCP_REVIEW_REQUIRED,
    MCP_BLOCKED_MISSING_SOURCE_INTENT,
    MCP_BLOCKED_MISSING_CANDIDATE,
    MCP_BLOCKED_PARSE_ERROR,
}

CONDITION_CATEGORIES = [
    "load_lifecycle",
    "boundary_lifecycle",
    "interaction_lifecycle",
    "amplitude_lifecycle",
    "step_procedure",
    "output_request",
    "reference_integrity",
    "target_patch_isolation",
]


def parse_target_change(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    parts = value.split(":")
    if len(parts) != 5:
        raise ValueError("target change must be type:load_name:step:from:to")
    change_type, load_name, step, from_value, to_value = parts
    return {
        "type": change_type,
        "load_name": load_name,
        "step": step,
        "from": from_value,
        "to": to_value,
    }


def validate_mcp_result(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if payload.get("stage") != STAGE:
        errors.append("stage must be Stage 4.5")
    if payload.get("guard_name") != GUARD_NAME:
        errors.append("guard_name is invalid")
    if payload.get("guard_short_name") != GUARD_SHORT_NAME:
        errors.append("guard_short_name is invalid")
    if payload.get("guard_status") not in VALID_GUARD_STATUSES:
        errors.append("guard_status is invalid")
    if not isinstance(payload.get("condition_findings"), list):
        errors.append("condition_findings must be a list")
    if payload.get("requires_human_review") is not True:
        errors.append("requires_human_review must be true")
    return {"valid": not errors, "errors": errors}
