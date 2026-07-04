from __future__ import annotations

from pathlib import Path
from typing import Any


def render_execution_report(result: dict[str, Any]) -> str:
    checks = result.get("checks", [])
    pass_items = "\n".join(f"- {item}" for item in result.get("pass_items", [])) or "- none"
    warning_items = "\n".join(f"- {item}" for item in result.get("warning_items", [])) or "- none"
    fail_items = "\n".join(f"- {item}" for item in result.get("fail_items", [])) or "- none"
    check_lines = "\n".join(f"- `{item.get('status')}` {item.get('name')}: {item.get('detail')}" for item in checks) or "- none"
    return f"""# Non-Solver Revalidation Execution Report

## Purpose
Execute deterministic Stage 5.0F revalidation for a supported non-solver downstream agent.

## Agent
`{result.get('downstream_agent')}`

## Input Scaffold
`{result.get('scaffold_path')}`

## Checks Executed
{check_lines}

## Pass / Warning / Fail Items
### Pass
{pass_items}

### Warning
{warning_items}

### Fail
{fail_items}

## Safety Boundary
No solver, QueueRunner, abqjobpilot GUI, enqueue, ODB open, Codex CLI call, LLM call, automatic scheduling, high-risk agent execution, or evidence approval occurred.

## Claim Boundary
`{result.get('result_status')}` means pending PipelineSupervisor review. It is not final evidence accepted.

## Result Status
`{result.get('result_status')}`

## Next Required Supervisor Action
{result.get('next_supervisor_action')}
"""


def render_run_record(result: dict[str, Any]) -> str:
    run_id = result["run_id"]
    agent_token = _agent_token(result["downstream_agent"])
    return f"""---
doc_type: run_report
task_id: {result['task_id']}
run_id: {run_id}
run_name: {agent_token}_REVALIDATION_RESULT
agent: {result['downstream_agent']}
status: {result['result_status']}
risk_level: LOW
handoff_in: {result.get('handoff_in_rel')}
handoff_out: {result.get('handoff_out_rel')}
gate_required_next: true
next_recommended_stage: pipeline_supervisor_review
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
automatic_execution_performed: false
final_evidence_approved: false
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

# {run_id} {agent_token} Revalidation Result

## Purpose
Execute deterministic non-solver revalidation for an ACOM accepted-pending-revalidation result.

## Inputs
- ACOM intake: `{result.get('acom_intake_path')}`
- structured result: `{result.get('structured_result_path')}`
- scaffold: `{result.get('scaffold_path')}`

## ACOM Intake Summary
`{result.get('intake_status')}`

## Revalidation Scaffold Summary
- downstream agent: `{result.get('downstream_agent')}`
- scaffold status: `{result.get('scaffold_status')}`

## Deterministic Checks Executed
{chr(10).join(f"- {item.get('name')}" for item in result.get('checks', []))}

## Check Results
- pass: {len(result.get('pass_items', []))}
- warning: {len(result.get('warning_items', []))}
- fail: {len(result.get('fail_items', []))}

## Outputs
- result JSON: `{result.get('result_path')}`
- report: `{result.get('report_path')}`
- gate: `{result.get('gate_path')}`
- handoff: `{result.get('handoff_path')}`

## Validation
Pipeline protocol validation: `{result.get('protocol_validation')}`

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, `shell=True`, automatic scheduling, high-risk downstream agent execution, or evidence approval occurred.

## Verdict
`{result.get('result_status')}`

## Claim Boundary
PASS means pending supervisor review, not final evidence accepted.

## Next Recommended Step
PipelineSupervisor reviews the result gate.
"""


def render_gate_record(result: dict[str, Any]) -> str:
    decision = "PENDING_SUPERVISOR_REVIEW" if result.get("result_status", "").endswith("PENDING_SUPERVISOR") else "BLOCKED"
    required = "true" if decision == "PENDING_SUPERVISOR_REVIEW" else "false"
    transition = f"{_agent_token(result['downstream_agent'])}_REVALIDATION_RESULT_TO_PIPELINE_SUPERVISOR"
    return f"""---
doc_type: gate_decision
task_id: {result['task_id']}
gate_id: {result['gate_id']}
transition: {transition}
risk_level: LOW
decision: {decision}
approver_type: PipelineSupervisor
human_approval_required: false
required_conditions_met: {required}
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
automatic_execution_performed: false
final_evidence_approved: false
---

# {result['gate_id']} {transition}

## Decision
{decision}

## Reason
Stage 5.0F non-solver deterministic revalidation produced `{result.get('result_status')}`.
"""


def render_handoff_record(result: dict[str, Any]) -> str:
    return f"""---
doc_type: handoff
task_id: {result['task_id']}
handoff_id: {result['handoff_id']}
from_agent: {result['downstream_agent']}
to_agent: PipelineSupervisor
from_run: {result['run_id']}
target_run: SUPERVISOR_REVIEW_PENDING
risk_level: LOW
gate_required_before_receiver_execution: true
gate_required_after_receiver_completion: true
expected_output: gates/{Path(result['gate_path']).name}
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
automatic_execution_performed: false
final_evidence_approved: false
---

# {result['handoff_id']} {result['downstream_agent']} Revalidation Result to PipelineSupervisor

## Context
Stage 5.0F deterministic non-solver revalidation has completed.

## Inputs for Receiver
- `{result.get('result_path')}`
- `{result.get('report_path')}`

## Required Task
Review the non-solver revalidation result. Do not treat it as final evidence approval.

## Forbidden Actions
Do not run solver, open ODB, call Codex CLI, auto-schedule agents, or approve final evidence.
"""


def render_summary_report(result: dict[str, Any]) -> str:
    return f"""# Non-Solver Revalidation Summary

## Status
`{result.get('result_status')}`

## Agent
`{result.get('downstream_agent')}`

## Revalidation Directory
`{result.get('revalidation_dir')}`

## Pipeline Records
- RUN: `{result.get('run_record_path')}`
- GATE: `{result.get('gate_path')}`
- HANDOFF: `{result.get('handoff_path')}`

## Claim Boundary
No final evidence was approved.
"""


def _agent_token(agent: str) -> str:
    token = agent
    append_agent = token.endswith("Agent")
    if append_agent:
        token = token[: -len("Agent")]
    chars: list[str] = []
    for index, ch in enumerate(token):
        if index and ch.isupper() and not token[index - 1].isupper():
            chars.append("_")
        chars.append(ch.upper())
    normalized = "".join(chars).replace("Q_A", "QA").replace("O_D_B", "ODB")
    return normalized + "_AGENT" if append_agent else normalized
