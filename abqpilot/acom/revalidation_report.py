from __future__ import annotations

from pathlib import Path
from typing import Any


def render_revalidation_plan(scaffold: dict[str, Any]) -> str:
    profile = scaffold["profile"]
    checks = "\n".join(f"- {item}" for item in profile["checklist"])
    forbidden = "\n".join(f"- {item}" for item in scaffold["forbidden_actions"])
    return f"""# ACOM Downstream Revalidation Plan

## Context
Accepted ACOM result requires deterministic downstream AbqPilot revalidation.

## Downstream Agent
`{scaffold['downstream_agent']}`

## Why This Revalidation Is Required
`{scaffold['intake_status']}` means accepted as structured input only. It is not final evidence.

## Inputs to Review
- `{scaffold['acom_intake_path']}`
- `{scaffold.get('structured_result_path')}`
- `{scaffold.get('source_handoff_path')}`

## Required Checks
{checks}

## Forbidden Actions
{forbidden}

## Expected Outputs
{chr(10).join(f"- {item}" for item in profile["expected_outputs"])}

## Gate Requirement
The downstream gate remains `{scaffold['gate_decision']}` until deterministic revalidation completes.
"""


def render_revalidation_inputs(scaffold: dict[str, Any]) -> str:
    return f"""# Revalidation Inputs

- task_id: `{scaffold['task_id']}`
- template_id: `{scaffold.get('template_id')}`
- intake_status: `{scaffold['intake_status']}`
- downstream_agent: `{scaffold['downstream_agent']}`
- ACOM intake: `{scaffold['acom_intake_path']}`
- structured result: `{scaffold.get('structured_result_path')}`
- source handoff: `{scaffold.get('source_handoff_path')}`
"""


def render_revalidation_checklist(scaffold: dict[str, Any]) -> str:
    checks = "\n".join(f"- [ ] {item}" for item in scaffold["profile"]["checklist"])
    return f"""# Revalidation Checklist

{checks}
"""


def render_expected_outputs(scaffold: dict[str, Any]) -> str:
    outputs = "\n".join(f"- `{item}`" for item in scaffold["profile"]["expected_outputs"])
    return f"""# Revalidation Expected Outputs

{outputs}

No downstream deterministic revalidation has been executed yet.
"""


def render_scaffold_report(scaffold: dict[str, Any]) -> str:
    return f"""# ACOM Downstream Revalidation Scaffold Report

This is a scaffold report.
No downstream deterministic revalidation has been executed yet.

## Status
`{scaffold['status']}`

## Downstream Agent
`{scaffold['downstream_agent']}`

## Package
`{scaffold['package_dir']}`

## Pipeline Records
- RUN: `{scaffold.get('run_record_path')}`
- GATE: `{scaffold.get('gate_path')}`
- HANDOFF: `{scaffold.get('handoff_path')}`

## Claim Boundary
Accepted ACOM result is not final evidence and does not approve solver, ODB, metrics, or final verdict.
"""


def render_run_record(scaffold: dict[str, Any]) -> str:
    run_id = scaffold["run_id"]
    profile = scaffold["profile"]
    return f"""---
doc_type: run_report
task_id: {scaffold['task_id']}
run_id: {run_id}
run_name: {profile['run_name']}
agent: {scaffold['downstream_agent']}
status: {scaffold['status']}
risk_level: {profile['risk_level']}
handoff_in: {scaffold['handoff_in_rel']}
handoff_out: {scaffold['handoff_out_rel']}
gate_required_next: true
next_recommended_stage: pipeline_supervisor_gate_review
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
automatic_execution_performed: false
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

# {run_id} {profile['run_name']}

## Purpose
Create a downstream revalidation scaffold for an accepted ACOM result.

## Inputs
- `{scaffold['acom_intake_path']}`
- `{scaffold.get('structured_result_path')}`

## ACOM Result Summary
Status: `{scaffold['intake_status']}`

## Downstream Agent Revalidation Scope
`{scaffold['downstream_agent']}`

## Required Deterministic Checks
{chr(10).join(f"- {item}" for item in profile['checklist'])}

## Generated Revalidation Package
`{scaffold['package_dir']}`

## Outputs
- `{scaffold.get('gate_path')}`
- `{scaffold.get('handoff_path')}`

## Validation
Pipeline protocol validation is expected after scaffold creation.

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, `shell=True`, automatic scheduling, downstream agent execution, or evidence approval occurred.

## Verdict
`{scaffold['status']}`

## Claim Boundary
This scaffold does not accept evidence. Codex summary is not final evidence.

## Next Recommended Step
PipelineSupervisor reviews the pending revalidation gate.
"""


def render_gate_record(scaffold: dict[str, Any]) -> str:
    return f"""---
doc_type: gate_decision
task_id: {scaffold['task_id']}
gate_id: {scaffold['gate_id']}
transition: ACOM_RESULT_TO_{_agent_token(scaffold['downstream_agent'])}_REVALIDATION
risk_level: {scaffold['profile']['risk_level']}
decision: {scaffold['gate_decision']}
approver_type: PipelineSupervisor
human_approval_required: false
required_conditions_met: false
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
downstream_agent: {scaffold['downstream_agent']}
automatic_execution_performed: false
---

# {scaffold['gate_id']} {scaffold['downstream_agent']} Revalidation

## Transition
ACOM accepted result to downstream revalidation scaffold.

## Decision
{scaffold['gate_decision']}

## Reason
Scaffold created for deterministic revalidation only. No evidence is approved.
"""


def render_handoff_record(scaffold: dict[str, Any]) -> str:
    return f"""---
doc_type: handoff
task_id: {scaffold['task_id']}
handoff_id: {scaffold['handoff_id']}
from_agent: {scaffold['downstream_agent']}
to_agent: {scaffold['profile']['next_agent']}
from_run: {scaffold['run_id']}
target_run: GATE_REVIEW_PENDING
risk_level: {scaffold['profile']['risk_level']}
gate_required_before_receiver_execution: true
gate_required_after_receiver_completion: true
expected_output: gates/{Path(scaffold['gate_path']).name}
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
automatic_execution_performed: false
---

# {scaffold['handoff_id']} {scaffold['downstream_agent']} Revalidation to {scaffold['profile']['next_agent']}

## Context
Downstream revalidation scaffold was created. No deterministic downstream revalidation has run yet.

## Inputs for Receiver
- `{scaffold['package_dir']}`
- `{scaffold['acom_intake_path']}`

## Required Task
Review the pending revalidation gate and decide the next deterministic step.

## Forbidden Actions
Do not auto-run agents, approve evidence, run solver, open ODB, call Codex CLI, or enqueue jobs.
"""


def _agent_token(agent: str) -> str:
    return agent.upper().replace("AGENT", "_AGENT").replace("__", "_")
