from __future__ import annotations

from pathlib import Path
from typing import Any


def render_non_solver_summary_report(summary: dict[str, Any]) -> str:
    entries = summary.get("ledger_entries", [])
    entry_lines = "\n".join(
        "- "
        f"agent=`{entry.get('source_revalidation_agent')}`, "
        f"revalidation=`{entry.get('source_revalidation_status')}`, "
        f"supervisor=`{entry.get('supervisor_review_status')}`, "
        f"decision=`{entry.get('ledger_decision')}`"
        for entry in entries
    ) or "- none"
    warnings = "\n".join(f"- {item}" for item in summary.get("warning_items", [])) or "- none"
    blocked = "\n".join(f"- {item}" for item in summary.get("blocked_items", [])) or "- none"
    lineage = summary.get("lineage", {})
    return f"""# EvidenceReportAgent Non-Solver Evidence Summary

This is a non-final, non-solver evidence summary.
It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

## Purpose
Summarize accepted `NON_SOLVER_EVIDENCE_LEDGER` entries without converting them into final evidence.

## Task
`{summary.get('task_id')}`

## Summary Scope
Non-solver ledger entries only. `TASK_FINAL_EVIDENCE_LEDGER.md` was not updated.

## Non-Solver Ledger Entries
{entry_lines}

## ACOM Lineage
- ACOM intake artifacts: `{', '.join(lineage.get('acom_intake_artifacts', [])) or 'not found'}`
- ACOM handoff artifacts: `{', '.join(lineage.get('acom_handoff_artifacts', [])) or 'not found'}`

## Revalidation Lineage
- Revalidation artifacts: `{', '.join(lineage.get('revalidation_artifacts', [])) or 'not found'}`

## Supervisor Review Lineage
- Supervisor artifacts: `{', '.join(lineage.get('supervisor_review_artifacts', [])) or 'not found'}`

## Pass / Warning / Blocked Items
### Pass
- ledger entries reviewed: `{summary.get('entries_reviewed')}`
- final evidence approved: `False`
- final verdict frozen: `False`
- solver approved: `False`
- ODB metrics approved: `False`

### Warning
{warnings}

### Blocked
{blocked}

## Claim Boundary
This report is non-final and non-solver only. It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

## Limitations
{warnings}

## Safety Boundary
No Abaqus solver, QueueRunner, abqjobpilot GUI, enqueue, ODB open, Codex CLI call, LLM provider call, automatic scheduling, high-risk downstream agent execution, final evidence approval, final verdict freeze, or final ledger update occurred.

## Next Required Action
`{summary.get('next_action')}`

## Result Status
`{summary.get('summary_status')}`
"""


def render_run_record(summary: dict[str, Any]) -> str:
    return f"""---
doc_type: run_report
task_id: {summary['task_id']}
run_id: {summary['run_id']}
run_name: EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY
agent: EvidenceReportAgent
status: {summary['summary_status']}
risk_level: LOW
handoff_in: {summary.get('handoff_in_rel')}
handoff_out: {summary.get('handoff_out_rel')}
gate_required_next: true
next_recommended_stage: pipeline_supervisor_non_solver_summary_ack
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
task_final_evidence_ledger_updated: false
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

# {summary['run_id']} EvidenceReportAgent Non-Solver Summary

## Purpose
Create a non-final, non-solver summary from `NON_SOLVER_EVIDENCE_LEDGER`.

## Inputs
- `{summary.get('ledger_json_path')}`
- `{summary.get('ledger_md_path')}`

## Non-Solver Ledger Summary
- entries reviewed: `{summary.get('entries_reviewed')}`
- summary status: `{summary.get('summary_status')}`

## Source Lineage Summary
- ACOM intake artifacts: `{len(summary.get('lineage', {}).get('acom_intake_artifacts', []))}`
- revalidation artifacts: `{len(summary.get('lineage', {}).get('revalidation_artifacts', []))}`
- supervisor review artifacts: `{len(summary.get('lineage', {}).get('supervisor_review_artifacts', []))}`

## Summary Checks Executed
{chr(10).join(f"- {item.get('name')}: {item.get('status')}" for item in summary.get('checks', [])) or "- none"}

## Generated Summary Report
`{summary.get('summary_report_path')}`

## Outputs
- `{summary.get('summary_result_path')}`
- `{summary.get('summary_report_path')}`
- `{summary.get('gate_path')}`
- `{summary.get('handoff_path')}`

## Validation
Pipeline protocol validation: `{summary.get('protocol_validation')}`

## Guardrails / Forbidden Actions Confirmation
No Codex CLI call, solver run, QueueRunner launch, ODB open, source CAE/INP mutation, `.env` read, `shell=True`, automatic scheduling, high-risk downstream agent execution, final evidence approval, final verdict freeze, or final ledger update occurred.

## Verdict
`{summary.get('summary_status')}`

## Claim Boundary
This is not the final evidence ledger and not a final verdict.

## Next Recommended Step
PipelineSupervisor may acknowledge this non-final summary in a future gate.
"""


def render_gate_record(summary: dict[str, Any]) -> str:
    required = "true" if summary.get("gate_decision") != "BLOCKED" else "false"
    return f"""---
doc_type: gate_decision
task_id: {summary['task_id']}
gate_id: {summary['gate_id']}
transition: NON_SOLVER_LEDGER_TO_EVIDENCE_REPORT_AGENT_SUMMARY
risk_level: LOW
decision: {summary['gate_decision']}
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
---

# {summary['gate_id']} EvidenceReportAgent Non-Solver Summary

## Decision
`{summary['gate_decision']}`

## Claim Boundary
This gate is pending PipelineSupervisor acknowledgement or blocked. It is never final evidence approval.
"""


def render_handoff_record(summary: dict[str, Any]) -> str:
    return f"""---
doc_type: handoff
task_id: {summary['task_id']}
handoff_id: {summary['handoff_id']}
from_agent: EvidenceReportAgent
to_agent: PipelineSupervisor
from_run: {summary['run_id']}
target_run: SUPERVISOR_NON_SOLVER_SUMMARY_ACK_PENDING
risk_level: LOW
gate_required_before_receiver_execution: false
gate_required_after_receiver_completion: true
expected_output: gates/GATE_XXX_SUPERVISOR_NON_SOLVER_SUMMARY_ACK.md
codex_summary_is_final_evidence: false
automatic_execution_performed: false
final_evidence_approved: false
final_verdict_frozen: false
solver_approved: false
odb_metrics_approved: false
task_final_evidence_ledger_updated: false
---

# {summary['handoff_id']} EvidenceReportAgent Non-Solver Summary to PipelineSupervisor

## Context
EvidenceReportAgent generated a non-final, non-solver summary from `NON_SOLVER_EVIDENCE_LEDGER`.

## Inputs for Receiver
- `{summary.get('summary_result_path')}`
- `{summary.get('summary_report_path')}`

## Required Task
Acknowledge or block the non-solver summary. Do not freeze final evidence or approve solver, ODB, metrics, or model mutation.
"""


def render_cli_summary_report(summary: dict[str, Any]) -> str:
    return f"""# Non-Solver Evidence Summary CLI Report

## Status
`{summary.get('summary_status')}`

## Task
`{summary.get('task_id')}`

## Ledger Entries
`{summary.get('entries_reviewed')}`

## Pipeline Records
- RUN: `{summary.get('run_record_path')}`
- GATE: `{summary.get('gate_path')}`
- HANDOFF: `{summary.get('handoff_path')}`

## Claim Boundary
This is a non-final, non-solver evidence summary.
It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.
"""


def rel_handoff(path_value: str | None) -> str:
    if not path_value:
        return "none"
    return f"handoffs/{Path(path_value).name}"
