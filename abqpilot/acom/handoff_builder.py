from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.acom.handoff_schema import (
    DEFAULT_SAFETY_FLAGS,
    EXECUTION_MODE_ACOM,
    REQUIRED_HANDOFF_FILES,
    REQUIRED_VALIDATORS,
    SCHEMA_VERSION,
    STAGE,
    output_contract_schema,
    validate_handoff_manifest,
)
from abqpilot.acom.task_templates import template_for_task_type, render_codex_task_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATUS = "PASS_ABQPILOT_V2_STAGE4_5_MODEL_CONDITION_PRESERVATION_GUARD_READY"


def generate_codex_handoff(
    *,
    task_id: str,
    task_type: str,
    output_dir: str | Path | None = None,
    title: str | None = None,
    objective: str | None = None,
    context: str | None = None,
    allowed_paths: list[str] | None = None,
    forbidden_paths: list[str] | None = None,
    allowed_commands: list[str] | None = None,
    forbidden_commands: list[str] | None = None,
    current_status: str = DEFAULT_STATUS,
    project_root: str | Path = PROJECT_ROOT,
) -> dict[str, Any]:
    template = template_for_task_type(task_type)
    root = Path(project_root)
    handoff_dir = Path(output_dir) if output_dir else root / "runs" / "tasks" / task_id / "codex_handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    allowed_paths_final = list(allowed_paths or [str(root)])
    forbidden_paths_final = list(forbidden_paths or [str(root / ".env"), str(root / "CAE_model" / "sanity_base" / "sanity_base_v01.cae")])
    allowed_commands_final = list(allowed_commands or template["allowed_commands"])
    forbidden_commands_final = list(forbidden_commands or template["forbidden_commands"])
    expected_outputs = template["expected_outputs"]
    title_final = title or f"ACOM {task_type} handoff"
    objective_final = objective or template["default_objective"]
    created_at = datetime.now().isoformat(timespec="seconds")
    handoff_id = _stable_id(task_id, task_type, created_at)

    files: dict[str, Any] = {
        "input_manifest.json": {
            "schema_version": SCHEMA_VERSION,
            "mode": EXECUTION_MODE_ACOM,
            "task_id": task_id,
            "task_type": task_type,
            "project_root": str(root),
            "context_provided": bool(context),
        },
        "allowed_paths.json": {"schema_version": SCHEMA_VERSION, "allowed_paths": allowed_paths_final},
        "forbidden_paths.json": {"schema_version": SCHEMA_VERSION, "forbidden_paths": forbidden_paths_final},
        "allowed_commands.json": {"schema_version": SCHEMA_VERSION, "allowed_commands": allowed_commands_final},
        "forbidden_commands.json": {"schema_version": SCHEMA_VERSION, "forbidden_commands": forbidden_commands_final},
        "expected_outputs.json": {"schema_version": SCHEMA_VERSION, "expected_outputs": expected_outputs},
        "evidence_contract.json": {
            "schema_version": SCHEMA_VERSION,
            "mode": EXECUTION_MODE_ACOM,
            "requires_structured_result_json": True,
            "requires_file_hashes": True,
            "requires_tests_result": True,
            "requires_safety_flags": True,
            "requires_secret_audit_result": True,
            "requires_mcpguard_result_for_model_mutation_or_inp_patch": True,
            "codex_summary_is_final_evidence": False,
            "abqpilot_revalidation_required": True,
        },
        "output_contract.schema.json": output_contract_schema(),
        "safety_contract.json": {
            "schema_version": SCHEMA_VERSION,
            "mode": EXECUTION_MODE_ACOM,
            "safety_flags": dict(DEFAULT_SAFETY_FLAGS),
            "forbidden_actions": template["forbidden_actions"],
        },
    }
    for name, payload in files.items():
        _write_json(handoff_dir / name, payload)

    codex_task = render_codex_task_markdown(
        project_root=str(root),
        current_status=current_status,
        task_id=task_id,
        task_type=task_type,
        title=title_final,
        objective=objective_final,
        allowed_paths=allowed_paths_final,
        forbidden_paths=forbidden_paths_final,
        allowed_commands=allowed_commands_final,
        forbidden_commands=forbidden_commands_final,
        expected_outputs=expected_outputs,
        context=context,
    )
    (handoff_dir / "codex_task.md").write_text(codex_task, encoding="utf-8")
    (handoff_dir / "acceptance_criteria.md").write_text(
        "# Acceptance Criteria\n\n"
        "- Structured result JSON validates.\n"
        "- All unsafe safety flags remain false.\n"
        "- Codex summary is not final evidence.\n"
        "- AbqPilot deterministic revalidation remains required.\n"
        "- MCPGuard is required when model conditions or INP patches may be affected.\n",
        encoding="utf-8",
    )
    if context:
        (handoff_dir / "context_summary.md").write_text(context, encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "execution_mode": EXECUTION_MODE_ACOM,
        "task_id": task_id,
        "handoff_id": handoff_id,
        "created_at": created_at,
        "project_root": str(root),
        "handoff_dir": str(handoff_dir),
        "task_type": task_type,
        "codex_task_path": str(handoff_dir / "codex_task.md"),
        "input_manifest_path": str(handoff_dir / "input_manifest.json"),
        "allowed_paths_path": str(handoff_dir / "allowed_paths.json"),
        "forbidden_paths_path": str(handoff_dir / "forbidden_paths.json"),
        "allowed_commands_path": str(handoff_dir / "allowed_commands.json"),
        "forbidden_commands_path": str(handoff_dir / "forbidden_commands.json"),
        "expected_outputs_path": str(handoff_dir / "expected_outputs.json"),
        "evidence_contract_path": str(handoff_dir / "evidence_contract.json"),
        "output_contract_schema_path": str(handoff_dir / "output_contract.schema.json"),
        "safety_contract_path": str(handoff_dir / "safety_contract.json"),
        "acceptance_criteria_path": str(handoff_dir / "acceptance_criteria.md"),
        "requires_human_operator": True,
        "codex_auto_execution_allowed": False,
        "abqpilot_validation_required": True,
        "codex_summary_is_final_evidence": False,
        "required_abqpilot_validators": list(REQUIRED_VALIDATORS),
        "safety_flags": dict(DEFAULT_SAFETY_FLAGS),
    }
    _write_json(handoff_dir / "handoff_manifest.json", manifest)
    valid, errors = validate_handoff_manifest(manifest)
    return {
        "command": "generate-codex-handoff",
        "verdict": "ACOM_HANDOFF_GENERATED" if valid else "ACOM_HANDOFF_INVALID",
        "success": valid,
        "errors": errors,
        "warnings": [],
        "handoff_dir": str(handoff_dir),
        "task_id": task_id,
        "task_type": task_type,
        "handoff_id": handoff_id,
        "required_files": list(REQUIRED_HANDOFF_FILES),
        "details": manifest,
    }


def validate_codex_handoff(handoff_dir: str | Path) -> dict[str, Any]:
    root = Path(handoff_dir)
    manifest_path = root / "handoff_manifest.json"
    errors: list[str] = []
    if not manifest_path.exists():
        errors.append("missing handoff_manifest.json")
        manifest: dict[str, Any] = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        valid, validation_errors = validate_handoff_manifest(manifest)
        errors.extend(validation_errors)
    for file_name in REQUIRED_HANDOFF_FILES:
        if not (root / file_name).exists():
            errors.append(f"missing required file: {file_name}")
    verdict = "ACOM_HANDOFF_VALID" if not errors else "ACOM_HANDOFF_INVALID"
    return {
        "command": "validate-codex-handoff",
        "verdict": verdict,
        "success": not errors,
        "errors": errors,
        "warnings": [],
        "handoff_dir": str(root),
        "details": manifest,
    }


def _stable_id(task_id: str, task_type: str, created_at: str) -> str:
    digest = hashlib.sha256(f"{task_id}|{task_type}|{created_at}".encode("utf-8")).hexdigest()[:16]
    return f"acom_{digest}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
