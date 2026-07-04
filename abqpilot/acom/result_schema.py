from __future__ import annotations

from typing import Any

from abqpilot.acom.handoff_schema import EXECUTION_MODE_ACOM, SCHEMA_VERSION


REQUIRED_RESULT_FIELDS = [
    "schema_version",
    "mode",
    "task_id",
    "handoff_id",
    "verdict",
    "files_created",
    "files_modified",
    "files_deleted",
    "commands_run",
    "tests_run",
    "artifacts",
    "safety_flags",
    "validation_claims",
    "final_status",
    "known_limitations",
]

SAFE_FALSE_FLAGS = [
    "solver_started",
    "queue_runner_launched",
    "abqjobpilot_gui_launched",
    "odb_opened",
    "env_read",
    "forbidden_path_touched",
    "source_sanity_base_mutated",
    "shell_true_used",
    "generic_subprocess_added",
    "codex_cli_auto_called",
    "final_evidence_frozen",
    "human_approval_fabricated",
    "approval_token_generated_by_codex",
]

RESULT_STATUSES = [
    "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
    "ACOM_RESULT_REJECTED_SCHEMA_INVALID",
    "ACOM_RESULT_REJECTED_SAFETY_FLAGS",
    "ACOM_RESULT_REJECTED_TASK_MISMATCH",
    "ACOM_RESULT_REJECTED_HANDOFF_MISMATCH",
    "ACOM_RESULT_BLOCKED_MISSING_RESULT",
    "ACOM_RESULT_BLOCKED_MISSING_HANDOFF",
    "ACOM_RESULT_BLOCKED_MISSING_ARTIFACTS",
    "ACOM_RESULT_REVIEW_REQUIRED",
]

VALIDATION_CLAIMS = [
    "schemas_valid",
    "tests_passed",
    "static_validator_passed",
    "diff_guard_passed",
    "physics_guard_passed",
    "mcpguard_passed_or_not_applicable",
    "safety_audit_passed",
    "secret_audit_passed",
]


def empty_structured_result(task_id: str, handoff_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": EXECUTION_MODE_ACOM,
        "task_id": task_id,
        "handoff_id": handoff_id,
        "verdict": "PASS",
        "files_created": [],
        "files_modified": [],
        "files_deleted": [],
        "commands_run": [],
        "tests_run": [],
        "artifacts": {},
        "safety_flags": {key: False for key in SAFE_FALSE_FLAGS},
        "validation_claims": {key: False for key in VALIDATION_CLAIMS},
        "final_status": "PLACEHOLDER_RESULT_FOR_SCHEMA_INTAKE",
        "known_limitations": [],
    }


def validate_structured_result(result: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for key in REQUIRED_RESULT_FIELDS:
        if key not in result:
            errors.append(f"missing required field: {key}")
    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if result.get("mode") != EXECUTION_MODE_ACOM:
        errors.append("mode must be ACOM")
    if result.get("verdict") not in {"PASS", "WARNING", "FAIL"}:
        errors.append("verdict must be PASS, WARNING, or FAIL")
    for key in ["files_created", "files_modified", "files_deleted", "commands_run", "tests_run", "known_limitations"]:
        if key in result and not isinstance(result[key], list):
            errors.append(f"{key} must be a list")
    if "artifacts" in result and not isinstance(result["artifacts"], dict):
        errors.append("artifacts must be an object")
    safety_flags = result.get("safety_flags")
    if not isinstance(safety_flags, dict):
        errors.append("safety_flags must be an object")
    else:
        for key in SAFE_FALSE_FLAGS:
            if key not in safety_flags:
                errors.append(f"missing safety flag: {key}")
    claims = result.get("validation_claims")
    if not isinstance(claims, dict):
        errors.append("validation_claims must be an object")
    else:
        for key in VALIDATION_CLAIMS:
            if key not in claims:
                errors.append(f"missing validation claim: {key}")
    return not errors, errors


def unsafe_safety_flags(result: dict[str, Any]) -> list[str]:
    flags = result.get("safety_flags") or {}
    return [key for key in SAFE_FALSE_FLAGS if flags.get(key) is True]
