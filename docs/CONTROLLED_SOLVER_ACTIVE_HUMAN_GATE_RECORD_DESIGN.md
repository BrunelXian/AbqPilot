# Controlled Solver Active Human Gate Record Design

Stage 5.2D defines active controlled solver human gate record design only.

It does not write a real active gate to any real task. It does not run solver. It does not create solver request files. It does not open ODB or extract metrics. It does not approve final evidence or freeze verdict.

## Design Boundary

The active gate schema describes what a future human approval record would look like. In Stage 5.2D:

- `active_record_created_in_stage_5_2d=false`
- `real_project_gate_written=false`
- `solver_execution_allowed=false`
- `solver_request_created=false`
- `solver_run=false`
- `queue_runner_launched=false`
- `odb_opened=false`
- `odb_metrics_approved=false`
- `final_evidence_approved=false`
- `final_verdict_frozen=false`
- `task_final_evidence_ledger_updated=false`
- `writer_enabled=false`

The schema may contain `solver_approved=true` only inside the design object to describe a future approved human gate. That design object is not written to real task `gates/`.

## Token Consumption

Token consumption does not execute solver.

Future token consumption must require:

- valid one-time token
- task ID binding
- candidate artifact hash binding
- exact approval phrase
- all acknowledgement flags
- no token reuse

Token consumption does not approve ODB, metrics, final evidence, or final verdict.

## Candidate Hash Binding

Candidate hash binding uses SHA256 for allowed candidate artifact paths. The helper blocks `.env`, ODB files, `queue.json`, `live_status.json`, `runtime/reports`, source sanity-base CAE, and source sanity-base INP.

## Future Handoff

The future execution handoff shape is design-only. It may target `ExecutionAgent`, but it is not written as an active execution handoff in Stage 5.2D.

Solver execution must be a later explicit stage. Human approval and solver execution remain separate.

## Output

Stage 5.2D writes non-final design/specification outputs under `gui_high_risk_gate_ux/controlled_solver_active_gate_design/`:

- `CONTROLLED_SOLVER_ACTIVE_GATE_SCHEMA.json`
- `CONTROLLED_SOLVER_ACTIVE_GATE_SCHEMA_REPORT.md`
- `CONTROLLED_SOLVER_ACTIVE_GATE_VALIDATION_RULES.md`
- `CONTROLLED_SOLVER_TOKEN_CONSUMPTION_RULES.md`
- `CONTROLLED_SOLVER_CANDIDATE_HASH_BINDING.md`
- `CONTROLLED_SOLVER_FUTURE_EXECUTION_HANDOFF_SHAPE.json`
- `CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_POLICY.md`

These files are not active gates, not solver requests, not active execution handoffs, and not final evidence.

## Fixture Writer Verification

Stage 5.2E adds fixture-only writer verification. It can write active gate records only under temporary pytest paths or clearly marked `tests/fixtures/` directories. Real task gate writes remain disabled, solver request files are not created, and solver execution remains a later explicit stage.

Stage 5.2F creates one real active human approval gate under the dedicated smoke task only. This gate may set `solver_approved=true`, but it keeps `solver_execution_allowed=false`, creates no solver request, and requires a future execution stage.

Stage 5.2G preserves that split: it creates a draft-only future execution handoff from the Stage 5.2F smoke gate and does not activate solver execution.

Stage 5.2H defines only the future request schema shape. It does not create active solver requests, job requests, or solver launchers.
