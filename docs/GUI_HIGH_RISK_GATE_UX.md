# GUI High-Risk Gate UX

Stage 5.2A specifies high-risk gate UX only.

This stage does not enable high-risk execution. It does not create real approving gates. It does not mutate task `gates/` records as approval records. It does not run solver, open ODB, queue jobs, call Codex CLI, auto-schedule agents, approve final evidence, approve metrics, approve ODB, approve solver, freeze verdict, or mutate `TASK_FINAL_EVIDENCE_LEDGER.md`.

All high-risk gate objects in Stage 5.2A are marked:

- `PREVIEW_ONLY`
- `SPECIFICATION_ONLY`
- `NOT_APPROVED`
- `NOT_EXECUTABLE`

## Locked Actions

The GUI high-risk gate catalog covers:

- `CONTROLLED_SOLVER_RUN`
- `QUEUE_JOB`
- `OPEN_ODB_FOR_DIAGNOSIS`
- `EXTRACT_ODB_METRICS`
- `MUTATE_SOURCE_CAE`
- `MUTATE_SOURCE_INP`
- `ACCEPT_METRICS_FOR_EVIDENCE`
- `APPROVE_FINAL_EVIDENCE`
- `FREEZE_FINAL_VERDICT`
- `DELETE_OR_OVERWRITE_HISTORICAL_ARTIFACT`
- `RUN_CODEX_FROM_GUI`
- `AUTO_SCHEDULE_AGENT`

Every action is disabled by default, not executable in Stage 5.2A, preview-only, and requires a future explicit human gate.

## Required UX Copy

The GUI and reports must make these boundaries visible:

- High-risk action locked.
- Preview only; not an approval.
- Human gate required in a future explicit stage.
- This GUI does not execute solver, ODB, queue, Codex, or final freeze.
- Final evidence remains locked.
- Prerequisites shown here are advisory/specification only.
- No real gate is created in Stage 5.2A.
- No `TASK_FINAL_EVIDENCE_LEDGER.md` mutation.

## Output

Stage 5.2A writes non-final specification outputs under `gui_high_risk_gate_ux/`:

- `HIGH_RISK_GATE_UX_SPEC.json`
- `HIGH_RISK_GATE_UX_SPEC_REPORT.md`
- `HIGH_RISK_ACTION_CATALOG.md`
- `HIGH_RISK_GATE_CHECKLISTS.md`

These are specification outputs only. Human gate approval must be introduced only in a future explicit stage.

## Controlled Solver Run Preview

Stage 5.2B narrows this catalog to `CONTROLLED_SOLVER_RUN` and defines a preview-only readiness checklist, inactive human approval token schema, token validation rules, and GUI preview card. It does not approve solver, run solver, create solver request files, create active approval gate records, open ODB, extract metrics, approve final evidence, or freeze verdict. Future real approval and future execution must be separate stages.

Stage 5.2C adds an inactive controlled solver human gate draft. It is not active approval, does not create active task `gates/` records, and keeps future active approval and future solver execution as separate later stages.
