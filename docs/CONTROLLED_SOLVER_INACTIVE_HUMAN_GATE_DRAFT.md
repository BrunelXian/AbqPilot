# Controlled Solver Inactive Human Gate Draft

Stage 5.2C creates an inactive controlled solver human gate draft only.

It does not approve solver. It does not run solver. It does not create solver request files. It does not create active approval gate records. It does not write active task `gates/` records. It does not open ODB or extract metrics. It does not approve final evidence or freeze verdict.

Every Stage 5.2C object is marked:

- `PREVIEW_ONLY`
- `INACTIVE_DRAFT`
- `NOT_APPROVED`
- `NOT_EXECUTABLE`
- `FUTURE_STAGE_REQUIRED`

## Draft Boundary

Inactive draft is not active approval. Inactive draft validation must block active approval attempts, active task gate output paths, executable solver request paths, queue mutation outputs, ODB metrics outputs, final evidence approval, and final verdict freeze.

## Future Shapes

The draft includes `expected_future_active_gate_shape` and `expected_future_solver_execution_handoff_shape` only as expected future shapes.

The future active gate shape may include `solver_approved=true`, but only inside `expected_future_active_gate_shape`. Stage 5.2C does not write that shape to task `gates/` as an active file.

The future solver execution handoff shape may target `ExecutionAgent`, but only as an expected future shape. Stage 5.2C does not write it as an active executable handoff.

## Required Separation

- Future active human approval gate creation must be a separate explicit stage.
- Future solver execution must be a later separate explicit stage.
- ODB and metrics remain disabled.
- Queue mutation remains disabled.
- Final evidence remains locked.

## Output

Stage 5.2C writes non-final inactive draft/specification outputs under `gui_high_risk_gate_ux/controlled_solver_inactive_gate_draft/`:

- `CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT.json`
- `CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_REPORT.md`
- `CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_VALIDATION.json`
- `CONTROLLED_SOLVER_FUTURE_ACTIVE_GATE_SHAPE.json`
- `CONTROLLED_SOLVER_FUTURE_EXECUTION_HANDOFF_SHAPE.json`

These files are not active gate records, not solver requests, and not execution handoffs.
