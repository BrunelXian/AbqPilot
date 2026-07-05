# GUI High-Risk Gate UX Specification

Stage 5.2A specifies high-risk gate UX only.

High-risk action locked.
Preview only; not an approval.
Human gate required in a future explicit stage.
This GUI does not execute solver, ODB, queue, Codex, or final freeze.
Final evidence remains locked.
Prerequisites shown here are advisory/specification only.
No real gate is created in Stage 5.2A.
No TASK_FINAL_EVIDENCE_LEDGER.md mutation.

## Safety Flags

- preview_only: `True`
- specification_only: `True`
- final_evidence_approved: `False`
- final_verdict_frozen: `False`
- solver_approved: `False`
- odb_metrics_approved: `False`
- queue_runner_launched: `False`
- codex_cli_called: `False`
- auto_execute_allowed: `False`
- real_gate_created: `False`
- task_final_evidence_ledger_updated: `False`

## High-Risk Actions

### Controlled Solver Run

- action_id: `CONTROLLED_SOLVER_RUN`
- risk_level: `HIGH`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Solver execution requires a future explicit human gate and fixed command approval.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Queue Job

- action_id: `QUEUE_JOB`
- risk_level: `HIGH`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Queue mutation and queue-worker lifecycle require a future explicit gate.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Open ODB for Diagnosis

- action_id: `OPEN_ODB_FOR_DIAGNOSIS`
- risk_level: `HIGH`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: ODB access remains gated and cannot be opened interactively in Stage 5.2A.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Extract ODB Metrics

- action_id: `EXTRACT_ODB_METRICS`
- risk_level: `HIGH`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Metrics extraction requires future ODB acceptance and metrics gate.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Mutate Source CAE

- action_id: `MUTATE_SOURCE_CAE`
- risk_level: `CRITICAL`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Source CAE mutation is irreversible-risk work and requires a future explicit source gate.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Mutate Source INP

- action_id: `MUTATE_SOURCE_INP`
- risk_level: `CRITICAL`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Source INP mutation must be separated from copied preview artifacts.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Accept Metrics for Evidence

- action_id: `ACCEPT_METRICS_FOR_EVIDENCE`
- risk_level: `CRITICAL`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Metric acceptance can affect final evidence and requires future supervisor gates.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Approve Final Evidence

- action_id: `APPROVE_FINAL_EVIDENCE`
- risk_level: `CRITICAL`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Final evidence approval is outside Stage 5.2A authority.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Freeze Final Verdict

- action_id: `FREEZE_FINAL_VERDICT`
- risk_level: `CRITICAL`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Final verdict freeze requires a future explicit final freeze stage.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Delete or Overwrite Historical Artifact

- action_id: `DELETE_OR_OVERWRITE_HISTORICAL_ARTIFACT`
- risk_level: `CRITICAL`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Historical artifact deletion/overwrite is destructive and requires a future explicit gate.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Run Codex from GUI

- action_id: `RUN_CODEX_FROM_GUI`
- risk_level: `HIGH`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: ACOM keeps Codex external/manual; GUI Codex execution requires a future runtime bridge design.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

### Auto Schedule Agent

- action_id: `AUTO_SCHEDULE_AGENT`
- risk_level: `HIGH`
- default_allowed: `False`
- executable_in_stage_5_2a: `False`
- preview_only: `True`
- requires_human_gate: `True`
- disabled_reason: Automatic scheduling is outside Stage 5.2A and requires a future orchestration design.
- final_evidence_effect: `FUTURE_STAGE_REQUIRED`

## Claim Boundary

This is a preview/specification record only. It is not solver readiness, ODB readiness, metrics readiness, queue readiness, Codex automation readiness, final evidence readiness, or final verdict freeze readiness.

Verdict: `PASS_ABQPILOT_V2_STAGE5_2A_GUI_HIGH_RISK_GATE_UX_SPEC_READY`
