from __future__ import annotations

from pathlib import Path
from typing import Any


def render_supervisor_review_report(review: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{item.get('status')}` {item.get('name')}: {item.get('detail')}" for item in review.get("checks", [])) or "- none"
    passes = "\n".join(f"- {item}" for item in review.get("pass_items", [])) or "- none"
    warnings = "\n".join(f"- {item}" for item in review.get("warning_items", [])) or "- none"
    failures = "\n".join(f"- {item}" for item in review.get("fail_items", [])) or "- none"
    return f"""# PipelineSupervisor Non-Solver Review Report

## Purpose
Review a completed Stage 5.0F non-solver revalidation result for possible non-final ledger entry.

## Task
`{review.get('task_id')}`

## Reviewed Revalidation Agent
`{review.get('reviewed_agent')}`

## Reviewed Status
`{review.get('reviewed_status')}`

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
No solver, QueueRunner, abqjobpilot GUI, enqueue, ODB open, Codex CLI call, LLM provider call, automatic scheduling, high-risk agent execution, final evidence approval, or final verdict freeze occurred.

## Ledger Decision
`{review.get('gate_decision')}`

## Claim Boundary
Accepted means accepted for the non-solver evidence ledger only. It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

## Result Status
`{review.get('review_status')}`

## Next Required Action
{review.get('next_action')}
"""


def render_run_record(review: dict[str, Any]) -> str:
    return f"""---
doc_type: run_report
task_id: {review['task_id']}
run_id: {review['run_id']}
run_name: PIPELINE_SUPERVISOR_NON_SOLVER_REVIEW
agent: PipelineSupervisor
status: {review['review_status']}
risk_level: LOW
handoff_in: {review.get('handoff_in_rel')}
handoff_out: {review.get('handoff_out_rel')}
gate_required_next: true
next_recommended_stage: evidence_report_agent_non_solver_summary
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
non_solver_ledger_entry_created: {str(review.get('non_solver_ledger_entry_created')).lower()}
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

# {review['run_id']} PipelineSupervisor Non-Solver Review

## Purpose
Review a Stage 5.0F non-solver revalidation result.

## Inputs
- `{review.get('source_revalidation_result_path')}`
- `{review.get('source_revalidation_report_path')}`

## Non-Solver Revalidation Result Summary
- agent: `{review.get('reviewed_agent')}`
- status: `{review.get('reviewed_status')}`

## Supervisor Checks Executed
{chr(10).join(f"- {item.get('name')}" for item in review.get('checks', []))}

## Ledger Decision
`{review.get('gate_decision')}`

## Generated Ledger Entry
`{review.get('non_solver_ledger_entry_created')}`

## Outputs
- `{review.get('review_result_path')}`
- `{review.get('review_report_path')}`
- `{review.get('ledger_md_path')}`

## Validation
Pipeline protocol validation: `{review.get('protocol_validation')}`

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, `shell=True`, automatic scheduling, high-risk downstream agent execution, final evidence approval, or final verdict freeze occurred.

## Verdict
`{review.get('review_status')}`

## Claim Boundary
This review can only accept non-solver ledger entries. It is not final evidence approval.

## Next Recommended Step
EvidenceReportAgent may summarize the non-solver ledger when an accepted handoff exists.
"""


def render_gate_record(review: dict[str, Any]) -> str:
    required = "true" if review.get("gate_decision") != "BLOCKED" else "false"
    return f"""---
doc_type: gate_decision
task_id: {review['task_id']}
gate_id: {review['gate_id']}
transition: NON_SOLVER_REVALIDATION_RESULT_TO_SUPERVISOR_LEDGER_REVIEW
risk_level: LOW
decision: {review['gate_decision']}
approver_type: PipelineSupervisor
human_approval_required: false
required_conditions_met: {required}
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
non_solver_ledger_entry_created: {str(review.get('non_solver_ledger_entry_created')).lower()}
---

# {review['gate_id']} Supervisor Non-Solver Review

## Decision
{review['gate_decision']}

## Claim Boundary
This gate is only for the non-solver evidence ledger. It is not final evidence approval.
"""


def render_handoff_record(review: dict[str, Any]) -> str:
    return f"""---
doc_type: handoff
task_id: {review['task_id']}
handoff_id: {review['handoff_id']}
from_agent: PipelineSupervisor
to_agent: EvidenceReportAgent
from_run: {review['run_id']}
target_run: NON_SOLVER_EVIDENCE_SUMMARY_PENDING
risk_level: LOW
gate_required_before_receiver_execution: false
gate_required_after_receiver_completion: true
expected_output: trace/RUN_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
---

# {review['handoff_id']} Supervisor Non-Solver Review to EvidenceReportAgent

## Context
PipelineSupervisor accepted a Stage 5.0F non-solver revalidation result for the non-solver evidence ledger.

## Inputs for Receiver
- `{review.get('review_result_path')}`
- `{review.get('ledger_md_path')}`

## Required Task
Prepare a non-final non-solver evidence summary. Do not freeze final evidence.
"""


def render_summary_report(review: dict[str, Any]) -> str:
    return f"""# PipelineSupervisor Non-Solver Review Summary

## Status
`{review.get('review_status')}`

## Reviewed Agent
`{review.get('reviewed_agent')}`

## Ledger Decision
`{review.get('gate_decision')}`

## Pipeline Records
- RUN: `{review.get('run_record_path')}`
- GATE: `{review.get('gate_path')}`
- HANDOFF: `{review.get('handoff_path')}`

## Claim Boundary
Accepted means non-solver ledger only, not final evidence.
"""


def handoff_rel(path_value: str | None) -> str:
    if not path_value:
        return "none"
    return f"handoffs/{Path(path_value).name}"
