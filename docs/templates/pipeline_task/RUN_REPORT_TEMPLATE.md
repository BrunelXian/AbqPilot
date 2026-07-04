---
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
