from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / "docs" / "templates" / "pipeline_task"


TEMPLATES: dict[str, str] = {
    "TASK_PLAN_TEMPLATE.md": """---
doc_type: task_plan
task_id: example_task
status: DRAFT
risk_level: LOW
---

# Task Plan

## Purpose

## Pipeline Scope

## Inputs

## Risk Level

## Expected Trace
""",
    "TRACE_INDEX_TEMPLATE.md": """---
doc_type: trace_index
task_id: example_task
status: DRAFT
---

# Trace Index

## Runs

## Handoffs

## Gates

## Artifact Directories
""",
    "RUN_REPORT_TEMPLATE.md": """---
doc_type: run_report
task_id: example_task
run_id: RUN_004
run_name: GUARD_VALIDATION
agent: GuardAgent
status: PASS
risk_level: HIGH
handoff_in: handoffs/HANDOFF_003_CANDIDATE_BUILDER_TO_GUARD.md
handoff_out: handoffs/HANDOFF_004_GUARD_TO_EXECUTION.md
gate_required_next: true
next_recommended_stage: execution
forbidden_actions:
  solver_run: false
  queue_runner_launched: false
  odb_opened: false
  source_cae_mutated: false
  source_inp_mutated: false
  env_read: false
  shell_true_used: false
---

# RUN Report

## Purpose

## Inputs

## Actions Taken

## Outputs

## Validation

## Guardrails / Forbidden Actions Confirmation

## Verdict

## Claim Boundary

## Next Recommended Step
""",
    "HANDOFF_TEMPLATE.md": """---
doc_type: handoff
task_id: example_task
handoff_id: HANDOFF_003
from_agent: CandidateBuilderAgent
to_agent: GuardAgent
from_run: RUN_003
target_run: RUN_004
risk_level: MEDIUM
gate_required_before_receiver_execution: false
gate_required_after_receiver_completion: true
expected_output: trace/RUN_004_GUARD_VALIDATION.md
---

# Handoff

## Context

## Inputs for Receiver

## Required Task

## Allowed Actions

## Forbidden Actions

## Required Outputs

## Acceptance Criteria

## Gate Requirement
""",
    "GATE_TEMPLATE.md": """---
doc_type: gate_decision
task_id: example_task
gate_id: GATE_002
transition: GUARD_VALIDATION_TO_EXECUTION
risk_level: HIGH
decision: PENDING
approver_type: HUMAN
human_approval_required: true
human_approval_token_valid: false
required_conditions_met: false
---

# Gate Decision

## Transition

## Risk Level

## Required Conditions

## Evidence Reviewed

## Decision

## Approver

## Reason

## Residual Risk
""",
    "TASK_FINAL_EVIDENCE_LEDGER_TEMPLATE.md": """---
doc_type: final_evidence_ledger
task_id: example_task
status: DRAFT
final_verdict: NOT_FROZEN
---

# Task Final Evidence Ledger

## Trace Inputs

## Handoff Inputs

## Gate Decisions

## Artifact Evidence

## Validator Evidence

## Diagnosis Evidence

## Metrics Evidence

## Known Limitations

## Final Verdict Recommendation
""",
}


def write_templates(root: str | Path | None = None) -> dict[str, str]:
    base = Path(root) if root is not None else PROJECT_ROOT
    target_dir = base / "docs" / "templates" / "pipeline_task"
    target_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, text in TEMPLATES.items():
        path = target_dir / name
        path.write_text(text, encoding="utf-8")
        paths[name] = str(path)
    return paths
