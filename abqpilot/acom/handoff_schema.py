from __future__ import annotations

from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0C"
EXECUTION_MODE_ACOM = "ACOM"
EXECUTION_MODE_NARM = "NARM"

REQUIRED_HANDOFF_FILES = [
    "codex_task.md",
    "input_manifest.json",
    "allowed_paths.json",
    "forbidden_paths.json",
    "allowed_commands.json",
    "forbidden_commands.json",
    "expected_outputs.json",
    "evidence_contract.json",
    "output_contract.schema.json",
    "safety_contract.json",
    "acceptance_criteria.md",
    "handoff_manifest.json",
]

REQUIRED_VALIDATORS = [
    "StaticValidator",
    "DiffGuard",
    "PhysicsGuard",
    "MCPGuard",
    "schema_validation",
    "safety_audit",
    "secret_audit",
]

DEFAULT_SAFETY_FLAGS = {
    "solver_run_allowed": False,
    "queue_runner_allowed": False,
    "abqjobpilot_gui_allowed": False,
    "odb_open_allowed": False,
    "env_read_allowed": False,
    "source_sanity_base_mutation_allowed": False,
    "generic_subprocess_allowed": False,
    "shell_true_allowed": False,
    "codex_cli_auto_call_allowed": False,
}

FORBIDDEN_ACTIONS = [
    "run Abaqus solver",
    "launch QueueRunner",
    "launch abqjobpilot GUI",
    "enqueue jobs",
    "submit jobs",
    "mutate abqjobpilot runtime queue/status/report files",
    "open ODB directly",
    "read or print .env",
    "mutate source sanity base CAE",
    "mutate source sanity base INP",
    "modify material",
    "modify geometry",
    "modify mesh",
    "arbitrary raw INP edit",
    "use shell=True",
    "add generic subprocess launcher",
    "add LangGraph",
    "add Agents SDK",
    "add Codex runtime bridge",
    "auto-call Codex CLI from AbqPilot",
]

SUPPORTED_TASK_TYPES = {
    "documentation_update",
    "diagnosis_review",
    "repair_proposal_review",
    "model_condition_guard_review",
    "abqjobpilot_record_audit",
    "test_expansion",
    "generic_safe_code_review",
    "stage_implementation",
    "read_only_audit",
    "guarded_candidate_preview",
    "controlled_execution_planning",
    "job_odb_diagnosis_review",
    "mcpguard_review",
    "docs_status_update",
    "safety_secret_audit",
}

HIGH_RISK_TASK_TYPES = {
    "solver_run",
    "solver_retry",
    "queue_enqueue",
    "repaired_inp_generation",
    "odb_metrics_extraction",
}


def execution_mode_acom() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE_ACOM,
        "codex_auto_execution_allowed": False,
        "requires_human_operator": True,
        "abqpilot_validation_required": True,
        "codex_summary_is_final_evidence": False,
    }


def execution_mode_narm() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE_NARM,
        "codex_cli_required": False,
        "native_runtime_executes_tools": True,
        "same_validation_contract_required": True,
    }


def output_contract_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "title": "ACOM structured result contract",
        "type": "object",
        "required": [
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
        ],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "mode": {"const": EXECUTION_MODE_ACOM},
            "verdict": {"enum": ["PASS", "WARNING", "FAIL"]},
        },
    }


def validate_handoff_manifest(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = [
        "schema_version",
        "stage",
        "execution_mode",
        "task_id",
        "handoff_id",
        "created_at",
        "project_root",
        "handoff_dir",
        "task_type",
        "codex_task_path",
        "input_manifest_path",
        "allowed_paths_path",
        "forbidden_paths_path",
        "allowed_commands_path",
        "forbidden_commands_path",
        "expected_outputs_path",
        "evidence_contract_path",
        "output_contract_schema_path",
        "safety_contract_path",
        "acceptance_criteria_path",
        "requires_human_operator",
        "codex_auto_execution_allowed",
        "abqpilot_validation_required",
        "codex_summary_is_final_evidence",
        "required_abqpilot_validators",
        "safety_flags",
    ]
    for key in required:
        if key not in manifest:
            errors.append(f"missing required field: {key}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if manifest.get("stage") != STAGE:
        errors.append("stage must be Stage 5.0A")
    if manifest.get("execution_mode") != EXECUTION_MODE_ACOM:
        errors.append("execution_mode must be ACOM")
    if manifest.get("task_type") in HIGH_RISK_TASK_TYPES:
        errors.append("high-risk task types are not supported in Stage 5.0A")
    if manifest.get("task_type") not in SUPPORTED_TASK_TYPES:
        errors.append("unsupported task_type")
    if manifest.get("requires_human_operator") is not True:
        errors.append("requires_human_operator must be true")
    if manifest.get("codex_auto_execution_allowed") is not False:
        errors.append("codex_auto_execution_allowed must be false")
    if manifest.get("abqpilot_validation_required") is not True:
        errors.append("abqpilot_validation_required must be true")
    if manifest.get("codex_summary_is_final_evidence") is not False:
        errors.append("codex_summary_is_final_evidence must be false")
    validators = set(manifest.get("required_abqpilot_validators") or [])
    for validator in REQUIRED_VALIDATORS:
        if validator not in validators:
            errors.append(f"required validator missing: {validator}")
    flags = manifest.get("safety_flags") or {}
    for key, value in DEFAULT_SAFETY_FLAGS.items():
        if flags.get(key) is not value:
            errors.append(f"safety flag {key} must be {value}")
    handoff_dir = Path(manifest.get("handoff_dir", ""))
    for file_name in REQUIRED_HANDOFF_FILES:
        if handoff_dir and not (handoff_dir / file_name).exists():
            errors.append(f"missing handoff file: {file_name}")
    return not errors, errors
