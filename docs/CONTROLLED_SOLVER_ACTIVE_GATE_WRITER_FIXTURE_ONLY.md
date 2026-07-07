# Controlled Solver Active Gate Writer Fixture Only

Stage 5.2E tests active gate writer in fixtures only.

Real task gate writes remain disabled. Fixture active gate records are not real solver approvals. Solver execution remains a future separate explicit stage.

## Fixture Scope

The writer supports `TEST_FIXTURE_ONLY` mode for temporary pytest directories and clearly marked `tests/fixtures/` paths. It refuses real task writes.

The fixture-written gate record must keep:

- `fixture_only=true`
- `real_project_gate_written=false`
- `active_record_created_in_stage_5_2e=true`
- `active_record_created_under_fixture=true`
- `real_task_gate_path=false`
- `solver_execution_allowed=false`
- `solver_request_created=false`
- `solver_run=false`
- `queue_runner_launched=false`
- `odb_opened=false`
- `odb_metrics_approved=false`
- `final_evidence_approved=false`
- `final_verdict_frozen=false`
- `task_final_evidence_ledger_updated=false`

`solver_approved=true` is allowed only inside fixture/test gate records and must not appear in a real project task gate created by Stage 5.2E.

## Blocking Policy

The writer blocks:

- `fixture_mode=false`
- real `runs/tasks/*/gates` paths
- `D:\Users\wuxia\Documents\AbqPilot`
- queue/runtime/status paths
- source sanity-base paths
- solver request creation
- execution handoff creation
- final evidence authority

## Safety Boundary

No solver request files are created. No Abaqus solver command is executed. No ODB/metrics/final evidence authority is granted. `TASK_FINAL_EVIDENCE_LEDGER.md remains untouched`.

## Output

Stage 5.2E writes non-final reports under `gui_high_risk_gate_ux/controlled_solver_active_gate_writer_fixture/`:

- `CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_POLICY.md`
- `CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_REPORT.md`
- `CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_RESULT.json`
- `CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_BLOCKED_REAL_TASK_REPORT.md`

These are fixture-policy reports only, not active project gates and not solver requests.

## Stage 5.2F Real Smoke Gate

Stage 5.2F allows a real active gate only for `runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/`. Arbitrary real task gate writing remains disabled. The smoke gate does not create a solver request and does not execute solver.

## Stage 5.2G Handoff Draft

Stage 5.2G continues this separation by creating only a draft execution handoff from the Stage 5.2F smoke gate. It does not create active execution handoffs or solver request files.
