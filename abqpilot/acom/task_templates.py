from __future__ import annotations

from typing import Any

from abqpilot.acom.handoff_schema import FORBIDDEN_ACTIONS, SUPPORTED_TASK_TYPES


DEFAULT_ALLOWED_COMMANDS = [
    "rg",
    "python -m pytest -q",
    "python -m pytest <targeted-tests> -q",
]

DEFAULT_FORBIDDEN_COMMANDS = [
    "codex",
    "abaqus",
    "abq2024",
    "QueueRunner",
    "run_gui",
    "openOdb",
    "session.openOdb",
    "subprocess with shell=True",
]


def template_for_task_type(task_type: str) -> dict[str, Any]:
    if task_type not in SUPPORTED_TASK_TYPES:
        raise ValueError(f"unsupported ACOM task type: {task_type}")
    objectives = {
        "documentation_update": "Update documentation within the bounded handoff scope.",
        "diagnosis_review": "Review diagnosis artifacts and produce structured findings only.",
        "repair_proposal_review": "Review repair proposal artifacts without applying repairs.",
        "model_condition_guard_review": "Review MCPGuard artifacts and preservation findings.",
        "abqjobpilot_record_audit": "Audit abqjobpilot records read-only and summarize structured evidence.",
        "test_expansion": "Add or review safe unit tests within the bounded handoff scope.",
        "generic_safe_code_review": "Review bounded code changes for defects and safety risks.",
    }
    expected_outputs = [
        "structured_result.json",
        "artifact hash list",
        "test result summary",
        "safety audit summary",
        "secret audit summary",
    ]
    return {
        "task_type": task_type,
        "default_objective": objectives[task_type],
        "allowed_commands": list(DEFAULT_ALLOWED_COMMANDS),
        "forbidden_commands": list(DEFAULT_FORBIDDEN_COMMANDS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "expected_outputs": expected_outputs,
    }


def render_codex_task_markdown(
    *,
    project_root: str,
    current_status: str,
    task_id: str,
    task_type: str,
    title: str,
    objective: str,
    allowed_paths: list[str],
    forbidden_paths: list[str],
    allowed_commands: list[str],
    forbidden_commands: list[str],
    expected_outputs: list[str],
    context: str | None = None,
) -> str:
    forbidden_actions = "\n".join(f"- {item}" for item in FORBIDDEN_ACTIONS)
    allowed_paths_md = "\n".join(f"- `{item}`" for item in allowed_paths) or "- none"
    forbidden_paths_md = "\n".join(f"- `{item}`" for item in forbidden_paths) or "- `.env` and secrets"
    allowed_commands_md = "\n".join(f"- `{item}`" for item in allowed_commands) or "- none"
    forbidden_commands_md = "\n".join(f"- `{item}`" for item in forbidden_commands) or "- none"
    outputs_md = "\n".join(f"- `{item}`" for item in expected_outputs)
    context_block = context or "No additional context provided."
    return f"""# {title}

## Project Root

`{project_root}`

## Current Accepted Status

`{current_status}`

## Task Objective

{objective}

## Execution Mode

ACOM = AbqPilot Codex Operator Mode.

Codex role: external bounded operator only. AbqPilot remains planner, validator, and evidence authority.

## Task Boundary

- task_id: `{task_id}`
- task_type: `{task_type}`
- Codex natural-language summary is not final evidence.
- AbqPilot will validate returned artifacts after execution.
- Target edit validation is insufficient; non-target original model conditions must be preserved and checked through MCPGuard when applicable.

## Context

{context_block}

## Allowed Files / Paths

{allowed_paths_md}

## Forbidden Files / Paths

{forbidden_paths_md}

## Allowed Commands

{allowed_commands_md}

## Forbidden Commands

{forbidden_commands_md}

## Safety Boundary

{forbidden_actions}

## Required Output Artifacts

{outputs_md}

## Evidence Contract

Codex must produce structured artifacts. Natural-language summaries are supporting notes only and are not final evidence.

## Acceptance Criteria

1. Required artifacts are present.
2. Structured result JSON conforms to `output_contract.schema.json`.
3. Safety flags remain false for solver, QueueRunner, GUI, ODB direct open, `.env` read, source sanity-base mutation, `shell=True`, generic subprocess, and Codex auto-call.
4. AbqPilot revalidation remains required.

## Required Final Report Format

Report files changed, artifacts written, tests run, safety flags, secret audit result, limitations, and final structured verdict.
"""
