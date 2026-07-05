# Controlled Solver Human Gate Preview

Stage 5.2B designs controlled solver gate preview and approval token schema only.

It does not approve solver. It does not run solver. It does not create solver request files. It does not create active approval gate records. It does not open ODB or extract metrics. It does not approve final evidence or freeze verdict.

Every Stage 5.2B object is preview-only:

- `PREVIEW_ONLY`
- `NOT_APPROVED`
- `NOT_EXECUTABLE`
- `FUTURE_STAGE_REQUIRED`

## Approval Token Boundary

The controlled solver approval token is preview-only in Stage 5.2B. Token validation can return `TOKEN_PREVIEW_VALID_FOR_FUTURE_STAGE`, but that is not active approval. If a token attempts `active_approval=true`, validation must return `TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT`.

## Separation of Stages

Future solver approval and future solver execution must be separate stages:

- Stage 5.2B: preview token and preview gate only.
- Future Stage 5.2C or later: real human approval gate record may be created, still no solver execution.
- Future Stage 5.2D or later: controlled solver execution may consume an approved gate, still no ODB or metrics approval.

Queue execution, ODB opening, metrics extraction, metrics acceptance, final evidence approval, and final verdict freeze remain separately gated.

## Required GUI Copy

- Controlled Solver Run is locked.
- Preview only; not a solver approval.
- Human approval token is not active in Stage 5.2B.
- No Abaqus solver command is executed.
- No solver request file is created.
- Future solver approval and future solver execution must be separate stages.
- Final evidence remains locked.
- ODB and metrics remain disabled.
- Queue mutation remains disabled.

## Output

Stage 5.2B writes non-final preview/specification outputs under `gui_high_risk_gate_ux/controlled_solver_gate_preview/`:

- `CONTROLLED_SOLVER_GATE_PREVIEW.json`
- `CONTROLLED_SOLVER_GATE_PREVIEW_REPORT.md`
- `CONTROLLED_SOLVER_READINESS_CHECKLIST.md`
- `CONTROLLED_SOLVER_APPROVAL_TOKEN_SCHEMA.json`
- `CONTROLLED_SOLVER_APPROVAL_TOKEN_RULES.md`

These files are not solver requests and are not approval gates.

## Inactive Gate Draft

Stage 5.2C turns this preview/token design into an inactive human gate draft. The draft remains preview-only, inactive, not approved, and not executable. It may include expected future active gate and future execution handoff shapes, but it does not write active task `gates/` records, create solver requests, or authorize solver execution.
