from __future__ import annotations

from pathlib import Path
from typing import Any


def render_supervisor_summary_ack_report(ack: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{item.get('status')}` {item.get('name')}: {item.get('detail')}" for item in ack.get("checks", [])) or "- none"
    passes = "\n".join(f"- {item}" for item in ack.get("pass_items", [])) or "- none"
    warnings = "\n".join(f"- {item}" for item in ack.get("warning_items", [])) or "- none"
    failures = "\n".join(f"- {item}" for item in ack.get("fail_items", [])) or "- none"
    return f"""# PipelineSupervisor Non-Solver Summary Acknowledgement Report

## Purpose
Acknowledge an EvidenceReportAgent non-solver summary as a non-final, non-solver project record.

## Task
`{ack.get('task_id')}`

## Reviewed Summary Status
`{ack.get('reviewed_summary_status')}`

## Reviewed Ledger Scope
`{ack.get('reviewed_entries_count')}` non-solver ledger entr(y/ies)

## Supervisor Checks
{checks}

## Pass / Warning / Fail Items
### Pass
{passes}

### Warning
{warnings}

### Fail
{failures}

## Safety Boundary
No solver, QueueRunner, abqjobpilot GUI, enqueue, ODB open, Codex CLI call, LLM provider call, automatic scheduling, high-risk agent execution, final evidence approval, final verdict freeze, or final ledger update occurred.

## Acknowledgement Decision
`{ack.get('gate_decision')}`

## Claim Boundary
Acknowledgement is non-final and non-solver only. It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

## Result Status
`{ack.get('ack_status')}`

## Next Required Action
{ack.get('next_action')}
"""


def render_run_record(ack: dict[str, Any]) -> str:
    return f"""---
doc_type: run_report
task_id: {ack['task_id']}
run_id: {ack['run_id']}
run_name: PIPELINE_SUPERVISOR_NON_SOLVER_SUMMARY_ACK
agent: PipelineSupervisor
status: {ack['ack_status']}
risk_level: LOW
handoff_in: {ack.get('handoff_in_rel')}
handoff_out: {ack.get('handoff_out_rel')}
gate_required_next: false
next_recommended_stage: docs_status_agent_status_sync
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
task_final_evidence_ledger_updated: false
non_solver_summary_ack_ledger_entry_created: {str(ack.get('non_solver_summary_ack_ledger_entry_created')).lower()}
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

# {ack['run_id']} PipelineSupervisor Non-Solver Summary Ack

## Purpose
Acknowledge an EvidenceReportAgent non-solver summary as a non-final record.

## Inputs
- `{ack.get('summary_result_path')}`
- `{ack.get('summary_report_path')}`
- `{ack.get('ledger_json_path')}`
- `{ack.get('ledger_md_path')}`

## Non-Solver Summary Review
- summary status: `{ack.get('reviewed_summary_status')}`
- summary gate: `{ack.get('reviewed_gate_decision')}`

## Supervisor Acknowledgement Checks
{chr(10).join(f"- {item.get('name')}: {item.get('status')}" for item in ack.get('checks', [])) or "- none"}

## Acknowledgement Decision
`{ack.get('gate_decision')}`

## Generated Acknowledgement Ledger Entry
`{ack.get('non_solver_summary_ack_ledger_entry_created')}`

## Outputs
- `{ack.get('ack_result_path')}`
- `{ack.get('ack_report_path')}`
- `{ack.get('ack_ledger_md_path')}`

## Validation
Pipeline protocol validation: `{ack.get('protocol_validation')}`

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, `shell=True`, automatic scheduling, high-risk downstream agent execution, final evidence approval, final verdict freeze, final ledger update, or TASK_FINAL_EVIDENCE_LEDGER mutation occurred.

## Verdict
`{ack.get('ack_status')}`

## Claim Boundary
This acknowledgement is not final evidence approval and not a final verdict.

## Next Recommended Step
DocsStatusAgent may synchronize project status documentation in a later non-solver step.
"""


def render_gate_record(ack: dict[str, Any]) -> str:
    required = "true" if ack.get("gate_decision") != "BLOCKED" else "false"
    return f"""---
doc_type: gate_decision
task_id: {ack['task_id']}
gate_id: {ack['gate_id']}
transition: NON_SOLVER_SUMMARY_TO_SUPERVISOR_ACK
risk_level: LOW
decision: {ack['gate_decision']}
approver_type: PipelineSupervisor
human_approval_required: false
required_conditions_met: {required}
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
task_final_evidence_ledger_updated: false
non_solver_summary_ack_ledger_entry_created: {str(ack.get('non_solver_summary_ack_ledger_entry_created')).lower()}
---

# {ack['gate_id']} Supervisor Non-Solver Summary Ack

## Decision
`{ack['gate_decision']}`

## Claim Boundary
This gate acknowledges a non-final, non-solver summary only. It is never final evidence approval.
"""


def render_handoff_record(ack: dict[str, Any]) -> str:
    return f"""---
doc_type: handoff
task_id: {ack['task_id']}
handoff_id: {ack['handoff_id']}
from_agent: PipelineSupervisor
to_agent: DocsStatusAgent
from_run: {ack['run_id']}
target_run: STATUS_SYNC_PENDING
risk_level: LOW
gate_required_before_receiver_execution: false
gate_required_after_receiver_completion: false
expected_output: PROJECT_STATUS_CURRENT.*
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
task_final_evidence_ledger_updated: false
---

# {ack['handoff_id']} Supervisor Non-Solver Summary Ack to DocsStatusAgent

## Context
PipelineSupervisor acknowledged a non-final, non-solver EvidenceReportAgent summary.

## Inputs for Receiver
- `{ack.get('ack_result_path')}`
- `{ack.get('ack_report_path')}`
- `{ack.get('ack_ledger_md_path')}`

## Required Task
Synchronize non-final project status documentation if requested. Do not update final evidence, approve solver, approve ODB, approve metrics, or freeze a verdict.
"""


def render_cli_ack_report(ack: dict[str, Any]) -> str:
    return f"""# Supervisor Non-Solver Summary Ack CLI Report

## Status
`{ack.get('ack_status')}`

## Task
`{ack.get('task_id')}`

## Summary Status
`{ack.get('reviewed_summary_status')}`

## Pipeline Records
- RUN: `{ack.get('run_record_path')}`
- GATE: `{ack.get('gate_path')}`
- HANDOFF: `{ack.get('handoff_path')}`

## Claim Boundary
This acknowledgement is non-final and non-solver only.
It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.
"""


def rel_handoff(path_value: str | None) -> str:
    if not path_value:
        return "none"
    return f"handoffs/{Path(path_value).name}"
