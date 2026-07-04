from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.acom.handoff_schema import DEFAULT_SAFETY_FLAGS, REQUIRED_HANDOFF_FILES, REQUIRED_VALIDATORS, output_contract_schema, validate_handoff_manifest
from abqpilot.acom.template_docs import render_template_description
from abqpilot.acom.template_registry import get_template
from abqpilot.acom.template_schema import AcomTemplate
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0C"


def render_pipeline_acom_handoff(
    *,
    task_id: str,
    template_id: str,
    project_root: str | Path = PROJECT_ROOT,
    title: str | None = None,
    objective: str | None = None,
    context: str | None = None,
    params: dict[str, Any] | None = None,
    allowed_paths: list[str] | None = None,
    forbidden_paths: list[str] | None = None,
    allowed_commands: list[str] | None = None,
    forbidden_commands: list[str] | None = None,
    run_id: str | None = None,
    handoff_id: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    template = get_template(template_id)
    task_dir = root / "runs" / "tasks" / task_id
    if not (task_dir / "TRACE_INDEX.md").exists():
        scaffold_pipeline_task(task_id, root=root)
    for child in ("trace", "handoffs", "gates", "codex_handoff", "codex_result", "artifacts"):
        (task_dir / child).mkdir(parents=True, exist_ok=True)
    run_id_final = run_id or "RUN_009"
    handoff_id_final = handoff_id or "HANDOFF_008"
    created_at = datetime.now().isoformat(timespec="seconds")
    run_name = f"ACOM_{template.template_id.upper()}"
    run_path = task_dir / "trace" / f"{run_id_final}_{run_name}.md"
    handoff_path = task_dir / "handoffs" / f"{handoff_id_final}_ACOM_TO_CODEX_OPERATOR.md"
    handoff_dir = task_dir / "codex_handoff"
    parameters = params or {}
    _validate_template_parameters(template, parameters)
    package = _write_codex_package(
        handoff_dir=handoff_dir,
        root=root,
        task_dir=task_dir,
        task_id=task_id,
        template=template,
        title=title,
        objective=objective,
        context=context,
        parameters=parameters,
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
        allowed_commands=allowed_commands,
        forbidden_commands=forbidden_commands,
        created_at=created_at,
    )
    run_path.write_text(_run_record(task_id, run_id_final, run_name, template, handoff_path), encoding="utf-8")
    handoff_path.write_text(_handoff_record(task_id, handoff_id_final, template), encoding="utf-8")
    gate_path = None
    if template.risk_level == "high" or template.pipeline_mapping.get("gate_required") or template.requires_mcpguard:
        gate_path = task_dir / "gates" / "GATE_005_PENDING_ACOM_RESULT_REVALIDATION.md"
        gate_path.write_text(_pending_gate(task_id, template), encoding="utf-8")
    valid, errors = validate_handoff_manifest(package["manifest"])
    return {
        "command": "generate-codex-handoff",
        "verdict": "ACOM_PIPELINE_HANDOFF_GENERATED" if valid else "ACOM_PIPELINE_HANDOFF_INVALID",
        "success": valid,
        "errors": errors,
        "warnings": [],
        "task_id": task_id,
        "task_type": template.template_id,
        "template_id": template.template_id,
        "handoff_id": package["manifest"]["handoff_id"],
        "handoff_dir": str(handoff_dir),
        "task_dir": str(task_dir),
        "run_record_path": str(run_path),
        "pipeline_handoff_path": str(handoff_path),
        "gate_path": str(gate_path) if gate_path else None,
        "details": package["manifest"],
    }


def _validate_template_parameters(template: AcomTemplate, params: dict[str, Any]) -> None:
    if template.template_id == "guarded_candidate_preview" and not template.requires_mcpguard and not params.get("mcpguard_not_applicable_reason"):
        raise ValueError("guarded_candidate_preview requires MCPGuard or an explicit not-applicable reason")


def _write_codex_package(
    *,
    handoff_dir: Path,
    root: Path,
    task_dir: Path,
    task_id: str,
    template: AcomTemplate,
    title: str | None,
    objective: str | None,
    context: str | None,
    parameters: dict[str, Any],
    allowed_paths: list[str] | None,
    forbidden_paths: list[str] | None,
    allowed_commands: list[str] | None,
    forbidden_commands: list[str] | None,
    created_at: str,
) -> dict[str, Any]:
    handoff_dir.mkdir(parents=True, exist_ok=True)
    allowed_paths_final = list(allowed_paths or [str(root), str(task_dir)])
    forbidden_paths_final = list(forbidden_paths or [str(root / ".env"), str(root / "CAE_model" / "sanity_base" / "sanity_base_v01.cae")])
    allowed_commands_final = list(allowed_commands or template.default_allowed_commands)
    forbidden_commands_final = list(forbidden_commands or template.default_forbidden_commands)
    evidence_contract = {
        "schema_version": SCHEMA_VERSION,
        "mode": "ACOM",
        "requires_structured_result_json": True,
        "requires_file_hashes": True,
        "requires_tests_result": True,
        "requires_safety_flags": True,
        "codex_summary_is_final_evidence": False,
        "abqpilot_revalidation_required": True,
    }
    evidence_contract.update(template.evidence_contract_overrides)
    files: dict[str, Any] = {
        "input_manifest.json": {
            "schema_version": SCHEMA_VERSION,
            "mode": "ACOM",
            "task_id": task_id,
            "task_type": template.template_id,
            "template_id": template.template_id,
            "project_root": str(root),
            "task_dir": str(task_dir),
            "parameters": parameters,
            "context_provided": bool(context),
        },
        "allowed_paths.json": {"schema_version": SCHEMA_VERSION, "allowed_paths": allowed_paths_final},
        "forbidden_paths.json": {"schema_version": SCHEMA_VERSION, "forbidden_paths": forbidden_paths_final},
        "allowed_commands.json": {"schema_version": SCHEMA_VERSION, "allowed_commands": allowed_commands_final},
        "forbidden_commands.json": {"schema_version": SCHEMA_VERSION, "forbidden_commands": forbidden_commands_final},
        "expected_outputs.json": {"schema_version": SCHEMA_VERSION, "expected_outputs": template.default_required_outputs},
        "evidence_contract.json": evidence_contract,
        "output_contract.schema.json": output_contract_schema(),
        "safety_contract.json": {
            "schema_version": SCHEMA_VERSION,
            "mode": "ACOM",
            "safety_flags": dict(DEFAULT_SAFETY_FLAGS),
            "forbidden_actions": template.default_forbidden_actions,
        },
    }
    for name, payload in files.items():
        _write_json(handoff_dir / name, payload)
    (handoff_dir / "codex_task.md").write_text(
        _codex_task_markdown(template, title, objective, context, root, task_dir, parameters, allowed_paths_final, forbidden_paths_final, allowed_commands_final, forbidden_commands_final),
        encoding="utf-8",
    )
    (handoff_dir / "acceptance_criteria.md").write_text(_acceptance(template), encoding="utf-8")
    (handoff_dir / "template_description.md").write_text(render_template_description(template), encoding="utf-8")
    handoff_id = _stable_id(task_id, template.template_id, created_at)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "execution_mode": "ACOM",
        "task_id": task_id,
        "handoff_id": handoff_id,
        "created_at": created_at,
        "project_root": str(root),
        "handoff_dir": str(handoff_dir),
        "task_type": template.template_id,
        "template_id": template.template_id,
        "template_version": template.template_version,
        "pipeline_task_dir": str(task_dir),
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
        "requires_pipeline_protocol": True,
        "required_abqpilot_validators": list(REQUIRED_VALIDATORS),
        "safety_flags": dict(DEFAULT_SAFETY_FLAGS),
        "pipeline_mapping": template.pipeline_mapping,
    }
    _write_json(handoff_dir / "handoff_manifest.json", manifest)
    return {"manifest": manifest}


def _codex_task_markdown(
    template: AcomTemplate,
    title: str | None,
    objective: str | None,
    context: str | None,
    root: Path,
    task_dir: Path,
    parameters: dict[str, Any],
    allowed_paths: list[str],
    forbidden_paths: list[str],
    allowed_commands: list[str],
    forbidden_commands: list[str],
) -> str:
    param_lines = "\n".join(f"- `{key}`: {value}" for key, value in sorted(parameters.items())) or "- none supplied"
    allowed_paths_md = "\n".join(f"- `{item}`" for item in allowed_paths)
    forbidden_paths_md = "\n".join(f"- `{item}`" for item in forbidden_paths)
    allowed_commands_md = "\n".join(f"- `{item}`" for item in allowed_commands)
    forbidden_commands_md = "\n".join(f"- `{item}`" for item in forbidden_commands)
    required_outputs = "\n".join(f"- `{item}`" for item in template.default_required_outputs)
    return f"""# {title or template.template_name}

## Project Root
`{root}`

## Pipeline Task Directory
`{task_dir}`

## Template
- template_id: `{template.template_id}`
- risk_level: `{template.risk_level}`
- producer_agent: `{template.pipeline_mapping.get('producer_agent')}`
- receiver_agent: `{template.pipeline_mapping.get('expected_receiver_agent')}`

## Objective
{objective or template.purpose}

## Context
{context or "No additional context provided."}

## Parameters
{param_lines}

## Allowed Files / Paths
{allowed_paths_md}

## Forbidden Files / Paths
{forbidden_paths_md}

## Allowed Commands
{allowed_commands_md}

## Forbidden Commands
{forbidden_commands_md}

## Required Output Artifacts
{required_outputs}

## Safety Boundary
- Codex executes externally and manually only.
- AbqPilot does not call Codex CLI.
- Codex auto execution is forbidden.
- No solver, QueueRunner, enqueue, abqjobpilot GUI, direct ODB open, or source CAE/INP/ODB mutation.
- Codex natural-language summary is not final evidence.
- AbqPilot revalidation is required.
- MCPGuard is required for model-condition or INP-patch related templates.

## Final Report Format
Report files changed, artifacts written, tests run, safety flags, secret audit result, limitations, and final structured verdict.
"""


def _acceptance(template: AcomTemplate) -> str:
    lines = "\n".join(f"- {item}" for item in template.default_acceptance_criteria)
    return f"""# Acceptance Criteria

{lines}

- `structured_result.json` must validate against `output_contract.schema.json`.
- Unsafe safety flags must remain false.
- Template `{template.template_id}` must return to AbqPilot for deterministic revalidation.
"""


def _run_record(task_id: str, run_id: str, run_name: str, template: AcomTemplate, handoff_path: Path) -> str:
    return f"""---
doc_type: run_report
task_id: {task_id}
run_id: {run_id}
run_name: {run_name}
agent: ACOMAgent
status: HANDOFF_GENERATED
risk_level: {template.risk_level.upper()}
handoff_out: handoffs/{handoff_path.name}
gate_required_next: {str(template.risk_level == "high" or template.pipeline_mapping.get("gate_required")).lower()}
codex_auto_execution_allowed: false
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

# {run_id} {run_name}

## Purpose
Generate a pipeline-integrated ACOM Codex handoff package for `{template.template_id}`.

## Inputs
- Template registry entry: `{template.template_id}`

## Actions Taken
- Created or updated `codex_handoff/`.
- Created this RUN record.
- Created ACOM-to-Codex HANDOFF record.

## Outputs
- `codex_handoff/handoff_manifest.json`
- `handoffs/{handoff_path.name}`

## Validation
The generated Codex handoff must validate with `validate-codex-handoff`.

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, or `shell=True` use occurred.

## Verdict
HANDOFF_GENERATED

## Claim Boundary
Codex summary is not final evidence. AbqPilot revalidation is required.

## Next Recommended Step
Human operator may run Codex externally and return `codex_result/structured_result.json` for ACOM intake.
"""


def _handoff_record(task_id: str, handoff_id: str, template: AcomTemplate) -> str:
    return f"""---
doc_type: handoff
task_id: {task_id}
handoff_id: {handoff_id}
from_agent: ACOMAgent
to_agent: CodexOperator
from_run: RUN_009
target_run: EXTERNAL_CODEX_OPERATOR
risk_level: {template.risk_level.upper()}
gate_required_before_receiver_execution: false
gate_required_after_receiver_completion: true
expected_output: codex_result/structured_result.json
codex_auto_execution_allowed: false
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
---

# {handoff_id} ACOM to Codex Operator

## Context
Pipeline-integrated ACOM handoff for `{template.template_id}`.

## Inputs for Receiver
- `codex_handoff/codex_task.md`
- `codex_handoff/input_manifest.json`
- `codex_handoff/safety_contract.json`
- `codex_handoff/evidence_contract.json`

## Required Task
Perform only the bounded external human-operated Codex task described by the handoff package.

## Allowed Actions
Use allowed paths and commands from the handoff package.

## Forbidden Actions
Do not call solver, QueueRunner, abqjobpilot GUI, enqueue, direct ODB open, source CAE/INP/ODB mutation, `.env` read, Codex auto execution, or `shell=True`.

## Required Outputs
- `codex_result/structured_result.json`
- Artifact references and hashes when applicable.

## Acceptance Criteria
Returned result must pass ACOM structured result intake and AbqPilot revalidation.

## Gate Requirement
Receiver completion requires AbqPilot revalidation before downstream evidence claims.
"""


def _pending_gate(task_id: str, template: AcomTemplate) -> str:
    return f"""---
doc_type: gate_decision
task_id: {task_id}
gate_id: GATE_005
transition: ACOM_RESULT_TO_ABQPILOT_REVALIDATION
risk_level: {template.risk_level.upper()}
decision: PENDING_REVALIDATION
approver_type: HUMAN
human_approval_required: true
human_approval_token_valid: false
required_conditions_met: false
---

# GATE_005 Pending ACOM Result Revalidation

## Transition
ACOM result intake to downstream AbqPilot validation.

## Risk Level
{template.risk_level.upper()}

## Required Conditions
- `codex_result/structured_result.json` exists.
- ACOM safety flags are safe.
- AbqPilot validators run as required.

## Evidence Reviewed
Pending.

## Decision
PENDING_REVALIDATION

## Approver
Human approval required where applicable.

## Reason
ACOM output is not final evidence.

## Residual Risk
Codex output may be incomplete or unsafe until deterministic revalidation passes.
"""


def _stable_id(task_id: str, template_id: str, created_at: str) -> str:
    digest = hashlib.sha256(f"{task_id}|{template_id}|{created_at}".encode("utf-8")).hexdigest()[:16]
    return f"acom_{digest}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
