from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.acom.handoff_builder import validate_codex_handoff
from abqpilot.acom.result_revalidation_gate import gate_decision_for_status
from abqpilot.acom.result_routing import handoff_agent_token, route_for_template
from abqpilot.acom.result_schema import unsafe_safety_flags, validate_structured_result


def intake_pipeline_acom_result(handoff_dir: str | Path, result_json: str | Path) -> dict[str, Any]:
    handoff_root = Path(handoff_dir)
    result_path = Path(result_json)
    manifest_path = handoff_root / "handoff_manifest.json"
    if not manifest_path.exists():
        return _blocked_missing_handoff(handoff_root, result_path)
    validation = validate_codex_handoff(handoff_root)
    manifest = validation.get("details") or {}
    task_dir = Path(manifest.get("pipeline_task_dir") or handoff_root.parent)
    result_dir = task_dir / "codex_result"
    if not result_path.exists():
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload={},
            status="ACOM_RESULT_BLOCKED_MISSING_RESULT",
            errors=[f"missing structured result JSON: {result_path}"],
            warnings=[],
            missing_artifacts=[],
        )
    try:
        result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload={},
            status="ACOM_RESULT_REJECTED_SCHEMA_INVALID",
            errors=[f"invalid JSON: {exc}"],
            warnings=[],
            missing_artifacts=[],
        )
    valid, schema_errors = validate_structured_result(result_payload)
    if not validation["success"]:
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_BLOCKED_MISSING_HANDOFF",
            errors=validation.get("errors", []),
            warnings=[],
            missing_artifacts=[],
        )
    if result_payload.get("task_id") != manifest.get("task_id"):
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_REJECTED_TASK_MISMATCH",
            errors=["result task_id does not match handoff manifest"],
            warnings=[],
            missing_artifacts=[],
        )
    if result_payload.get("handoff_id") != manifest.get("handoff_id"):
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_REJECTED_HANDOFF_MISMATCH",
            errors=["result handoff_id does not match handoff manifest"],
            warnings=[],
            missing_artifacts=[],
        )
    unsafe = unsafe_safety_flags(result_payload)
    if unsafe:
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_REJECTED_SAFETY_FLAGS",
            errors=[],
            warnings=[f"unsafe safety flags: {', '.join(unsafe)}"],
            missing_artifacts=[],
            unsafe_flags=unsafe,
        )
    if not valid or schema_errors:
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_REJECTED_SCHEMA_INVALID",
            errors=schema_errors,
            warnings=[],
            missing_artifacts=[],
        )
    outside_allowed = _paths_outside_allowed(result_payload, handoff_root, task_dir)
    if outside_allowed:
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_REJECTED_SAFETY_FLAGS",
            errors=[],
            warnings=[f"declared file paths outside allowed paths: {', '.join(outside_allowed)}"],
            missing_artifacts=[],
            unsafe_flags=["declared_path_outside_allowed_paths"],
        )
    missing_artifacts = _missing_artifacts(result_payload, task_dir)
    if missing_artifacts:
        return _write_pipeline_outputs(
            task_dir=task_dir,
            handoff_dir=handoff_root,
            result_path=result_path,
            manifest=manifest,
            result_payload=result_payload,
            status="ACOM_RESULT_BLOCKED_MISSING_ARTIFACTS",
            errors=[f"missing artifact: {item}" for item in missing_artifacts],
            warnings=[],
            missing_artifacts=missing_artifacts,
        )
    return _write_pipeline_outputs(
        task_dir=task_dir,
        handoff_dir=handoff_root,
        result_path=result_path,
        manifest=manifest,
        result_payload=result_payload,
        status="ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        errors=[],
        warnings=["Accepted only as structured input for AbqPilot revalidation."],
        missing_artifacts=[],
    )


def write_acom_result_intake_report(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    intake_path = task / "codex_result" / "acom_result_intake.json"
    if not intake_path.exists():
        return {
            "command": "report-acom-result-intake",
            "verdict": "ACOM_RESULT_INTAKE_REPORT_MISSING",
            "success": False,
            "errors": [f"missing intake artifact: {intake_path}"],
            "warnings": [],
            "task_dir": str(task),
            "details": {},
        }
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    report_path = task / "codex_result" / "acom_result_intake_report.md"
    report_path.write_text(_intake_report_markdown(intake), encoding="utf-8")
    return {
        "command": "report-acom-result-intake",
        "verdict": "ACOM_RESULT_INTAKE_REPORT_READY",
        "success": True,
        "errors": [],
        "warnings": intake.get("warnings", []),
        "task_dir": str(task),
        "report_path": str(report_path),
        "details": intake,
    }


def _blocked_missing_handoff(handoff_root: Path, result_path: Path) -> dict[str, Any]:
    return {
        "command": "intake-codex-result",
        "verdict": "ACOM_RESULT_BLOCKED_MISSING_HANDOFF",
        "success": False,
        "errors": [f"missing handoff_manifest.json: {handoff_root / 'handoff_manifest.json'}"],
        "warnings": [],
        "handoff_dir": str(handoff_root),
        "result_json": str(result_path),
        "details": {"abqpilot_revalidation_required": True},
    }


def _write_pipeline_outputs(
    *,
    task_dir: Path,
    handoff_dir: Path,
    result_path: Path,
    manifest: dict[str, Any],
    result_payload: dict[str, Any],
    status: str,
    errors: list[str],
    warnings: list[str],
    missing_artifacts: list[str],
    unsafe_flags: list[str] | None = None,
) -> dict[str, Any]:
    task_dir.mkdir(parents=True, exist_ok=True)
    for child in ("trace", "handoffs", "gates", "codex_result"):
        (task_dir / child).mkdir(parents=True, exist_ok=True)
    template_id = manifest.get("template_id") or manifest.get("task_type")
    route = route_for_template(template_id, manifest.get("task_type"))
    downstream = route["primary_downstream_agent"]
    run_id = _next_available_id(task_dir / "trace", "RUN", 10)
    handoff_id = _next_available_id(task_dir / "handoffs", "HANDOFF", 9)
    gate_id = _next_available_id(task_dir / "gates", "GATE", 6)
    downstream_token = handoff_agent_token(downstream)
    run_path = task_dir / "trace" / f"{run_id}_ACOM_RESULT_INTAKE.md"
    handoff_path = task_dir / "handoffs" / f"{handoff_id}_ACOM_RESULT_TO_{downstream_token}.md"
    gate_path = task_dir / "gates" / f"{gate_id}_ACOM_RESULT_REVALIDATION.md"
    decision, required_conditions_met = gate_decision_for_status(status)
    intake = {
        "schema_version": "0.1",
        "task_id": manifest.get("task_id") or result_payload.get("task_id"),
        "handoff_id": manifest.get("handoff_id"),
        "template_id": template_id,
        "result_status": status,
        "accepted_as_evidence": False,
        "abqpilot_revalidation_required": True,
        "codex_summary_is_final_evidence": False,
        "unsafe_safety_flags": unsafe_flags or [],
        "missing_artifacts": missing_artifacts,
        "errors": errors,
        "warnings": warnings,
        "routing": route,
        "downstream_agent": downstream,
        "gate_decision": decision,
        "required_conditions_met": required_conditions_met,
        "handoff_dir": str(handoff_dir),
        "result_json": str(result_path),
        "run_record_path": str(run_path),
        "gate_path": str(gate_path),
        "downstream_handoff_path": str(handoff_path),
    }
    intake_path = task_dir / "codex_result" / "acom_result_intake.json"
    intake_path.write_text(json.dumps(intake, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path = task_dir / "codex_result" / "acom_result_intake_report.md"
    report_path.write_text(_intake_report_markdown(intake), encoding="utf-8")
    run_path.write_text(_run_markdown(intake, run_id, handoff_path, _acom_operator_handoff(task_dir)), encoding="utf-8")
    gate_path.write_text(_gate_markdown(intake, gate_id, decision, required_conditions_met), encoding="utf-8")
    handoff_path.write_text(_handoff_markdown(intake, handoff_id, run_id, downstream, gate_path.name), encoding="utf-8")
    return {
        "command": "intake-codex-result",
        "verdict": status,
        "success": status == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        "errors": errors,
        "warnings": warnings,
        "handoff_dir": str(handoff_dir),
        "result_json": str(result_path),
        "report_path": str(report_path),
        "details": intake,
    }


def _missing_artifacts(result: dict[str, Any], task_dir: Path) -> list[str]:
    missing: list[str] = []
    artifacts = result.get("artifacts") or {}
    for value in artifacts.values():
        if isinstance(value, str):
            candidates = [Path(value)]
        elif isinstance(value, list):
            candidates = [Path(item) for item in value if isinstance(item, str)]
        else:
            candidates = []
        for path in candidates:
            if not path.is_absolute():
                path = task_dir / path
            if not path.exists():
                missing.append(str(path))
    return missing


def _paths_outside_allowed(result: dict[str, Any], handoff_dir: Path, task_dir: Path) -> list[str]:
    allowed_file = handoff_dir / "allowed_paths.json"
    if not allowed_file.exists():
        return []
    try:
        allowed_payload = json.loads(allowed_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    allowed_values = allowed_payload.get("allowed_paths") if isinstance(allowed_payload, dict) else allowed_payload
    if not isinstance(allowed_values, list):
        return []
    allowed_roots = [_normalize_path(Path(value), task_dir) for value in allowed_values if isinstance(value, str)]
    if not allowed_roots:
        return []
    outside: list[str] = []
    for field in ("files_created", "files_modified", "files_deleted"):
        for value in result.get(field) or []:
            if not isinstance(value, str):
                continue
            path = _normalize_path(Path(value), task_dir)
            if not any(_is_relative_to(path, root) or path == root for root in allowed_roots):
                outside.append(value)
    return outside


def _normalize_path(path: Path, task_dir: Path) -> Path:
    if not path.is_absolute():
        path = task_dir / path
    return path.resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _next_available_id(directory: Path, prefix: str, start: int) -> str:
    number = start
    while any(directory.glob(f"{prefix}_{number:03d}_*.md")):
        number += 1
    return f"{prefix}_{number:03d}"


def _acom_operator_handoff(task_dir: Path) -> str:
    candidates = sorted((task_dir / "handoffs").glob("HANDOFF_*_ACOM_TO_CODEX_OPERATOR.md"))
    if candidates:
        return f"handoffs/{candidates[-1].name}"
    return "handoffs/HANDOFF_XXX_ACOM_TO_CODEX_OPERATOR.md"


def _intake_report_markdown(intake: dict[str, Any]) -> str:
    return f"""# ACOM Result Intake Report

## Result Status
`{intake.get('result_status')}`

## Task
- task_id: `{intake.get('task_id')}`
- handoff_id: `{intake.get('handoff_id')}`
- template_id: `{intake.get('template_id')}`

## Safety Flags
- unsafe_safety_flags: `{', '.join(intake.get('unsafe_safety_flags') or []) or 'none'}`

## Artifact Review
- missing_artifacts: `{', '.join(intake.get('missing_artifacts') or []) or 'none'}`

## Routing
- downstream_agent: `{intake.get('downstream_agent')}`
- route: `{', '.join(intake.get('routing', {}).get('downstream_agents', []))}`

## Gate Decision
`{intake.get('gate_decision')}`

## Claim Boundary
Accepted ACOM result means accepted for deterministic AbqPilot revalidation, not accepted as final evidence.
"""


def _run_markdown(intake: dict[str, Any], run_id: str, handoff_path: Path, handoff_in: str) -> str:
    return f"""---
doc_type: run_report
task_id: {intake.get('task_id')}
run_id: {run_id}
run_name: ACOM_RESULT_INTAKE
agent: ACOMAgent
status: {intake.get('result_status')}
risk_level: MEDIUM
handoff_in: {handoff_in}
handoff_out: handoffs/{handoff_path.name}
gate_required_next: true
next_recommended_stage: abqpilot_revalidation
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
forbidden_actions:
  codex_cli_called: false
  solver_run: false
  queue_runner_launched: false
  odb_opened: false
  source_cae_mutated: false
  source_inp_mutated: false
  env_read: false
  shell_true_used: false
---

# {run_id} ACOM_RESULT_INTAKE

## Purpose
Classify Codex structured result for AbqPilot revalidation.

## Inputs
- `codex_handoff/handoff_manifest.json`
- `codex_result/structured_result.json`

## Structured Result Summary
Status: `{intake.get('result_status')}`

## Safety Flag Review
Unsafe flags: `{', '.join(intake.get('unsafe_safety_flags') or []) or 'none'}`

## Artifact Existence Review
Missing artifacts: `{', '.join(intake.get('missing_artifacts') or []) or 'none'}`

## Routing Decision
Downstream agent: `{intake.get('downstream_agent')}`

## Outputs
- `codex_result/acom_result_intake.json`
- `{handoff_path.as_posix()}`

## Validation
Schema, task id, handoff id, safety flags, and artifact paths were checked.

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, or `shell=True` use occurred.

## Verdict
`{intake.get('result_status')}`

## Claim Boundary
Accepted result is accepted only for deterministic AbqPilot revalidation, not final evidence.

## Next Recommended Step
Downstream AbqPilot agent revalidation.
"""


def _gate_markdown(intake: dict[str, Any], gate_id: str, decision: str, required_conditions_met: bool) -> str:
    return f"""---
doc_type: gate_decision
task_id: {intake.get('task_id')}
gate_id: {gate_id}
transition: ACOM_RESULT_INTAKE_TO_ABQPILOT_REVALIDATION
risk_level: MEDIUM
decision: {decision}
approver_type: PipelineSupervisor
human_approval_required: false
required_conditions_met: {str(required_conditions_met).lower()}
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
downstream_agent: {intake.get('downstream_agent')}
---

# {gate_id} ACOM Result Revalidation

## Transition
ACOM result intake to AbqPilot revalidation.

## Risk Level
MEDIUM

## Required Conditions
Structured result schema, handoff match, task match, safety flags, and artifact review must pass.

## Evidence Reviewed
- `codex_result/acom_result_intake.json`

## Decision
{decision}

## Approver
PipelineSupervisor

## Reason
Result status: `{intake.get('result_status')}`

## Residual Risk
Codex output is not evidence until downstream deterministic revalidation completes.

## Downstream Revalidation Requirement
Route to `{intake.get('downstream_agent')}`.
"""


def _handoff_markdown(intake: dict[str, Any], handoff_id: str, run_id: str, downstream: str, gate_name: str) -> str:
    expected_run = intake.get("routing", {}).get("revalidation_run_name", "ABQPILOT_REVALIDATION")
    return f"""---
doc_type: handoff
task_id: {intake.get('task_id')}
handoff_id: {handoff_id}
from_agent: ACOMAgent
to_agent: {downstream}
from_run: {run_id}
target_run: RUN_REVALIDATION_PENDING
risk_level: MEDIUM
gate_required_before_receiver_execution: true
gate_required_after_receiver_completion: true
expected_output: trace/RUN_XXX_{expected_run}.md
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
---

# {handoff_id} ACOM Result to {downstream}

## Context
ACOM result was intaken and classified as `{intake.get('result_status')}`.

## Inputs for Receiver
- `codex_result/acom_result_intake.json`
- `codex_result/structured_result.json`
- `codex_handoff/handoff_manifest.json`

## Required Revalidation Task
Perform deterministic AbqPilot revalidation for `{intake.get('template_id')}`.

## Allowed Actions
Read ACOM artifacts and run only the downstream agent's normal deterministic checks.

## Forbidden Actions
Do not treat Codex summary as evidence, run solver, open ODB, enqueue jobs, call Codex CLI, or auto-schedule other agents.

## Required Outputs
- `{expected_run}` RUN record.

## Acceptance Criteria
Downstream agent independently validates artifacts and records limitations.

## Gate Requirement
Use `gates/{gate_name}`.
"""
