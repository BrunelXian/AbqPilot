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

Stage 5.2D defines the active controlled solver human gate record design. It does not write real active task gates, create solver request files, write active execution handoffs, run solver, open ODB, approve metrics, approve final evidence, or freeze verdict. The GUI may show active gate schema, token consumption rules, candidate hash binding, and future handoff shape as design-only previews.

Stage 5.2E adds an Active Gate Writer [TEST FIXTURE ONLY] display. Real task writes remain disabled, fixture active gate records are not real solver approvals, and no Create Real Active Gate, Approve Solver, Approve and Run, or Run Solver callbacks are added.

Stage 5.2F adds a Controlled Solver Human Gate [SMOKE TASK CREATED] display. The active gate exists only in the Stage 5.2F smoke task, solver execution remains disabled, no solver request is created, future execution stage is required, and final evidence remains locked.

Stage 5.2G adds a Controlled Solver Execution Handoff Draft [DRAFT ONLY] display. The draft is not active for execution, no solver request is created, no solver execution occurs, a future ExecutionAgent stage is required, and final evidence remains locked.

Stage 5.2H adds a Controlled Solver Request Draft Schema [DRAFT ONLY] display. The draft schema is not an active solver request, no `solver_request.json` is created, no solver execution occurs, a future ExecutionAgent stage is required, and final evidence remains locked.

Stage 5.2I adds a Controlled Solver Request Preflight [NO EXECUTION] display. It may show source gate, handoff draft, request draft, candidate hash, command label, output policy, and resource policy checks, but it must also show that no active request, no output execution directory, and no solver execution are created.

Stage 5.2J adds a Controlled Solver Dry-Run Request [NO EXECUTION] display. The GUI must label it as dry-run-only and no-execution; it must not expose Run Solver, Submit Queue, Execute Request, Approve and Run, active request activation, queue submission, or generic execute callbacks.

Stage 5.3A-v2 adds a guarded Controlled Solver Demo Smoke Run status card for the dedicated v2 task. The GUI card is report/status oriented and must keep arbitrary task execution, generic Run Solver, Approve and Run, QueueRunner, ODB opening, metrics extraction, and final evidence controls disabled.
