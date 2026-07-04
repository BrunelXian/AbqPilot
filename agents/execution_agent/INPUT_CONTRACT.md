# ExecutionAgent Input Contract

## What the agent may receive
- Guard handoff.
- Approved gate decision.
- Controlled execution contract.

## Required upstream handoff
`handoffs/HANDOFF_004_GUARD_TO_EXECUTION.md`

## Required artifacts
- Guard PASS artifacts.
- `gates/GATE_002_ALLOW_EXECUTION.md` when execution is high risk.

## Required frontmatter fields
Gate frontmatter must include `decision`, `approver_type`, `human_approval_required`, `human_approval_token_valid`, and `required_conditions_met`.

## Input validation obligations
Confirm approval token validity and controlled path before any execution.

## Missing-input behavior
Stop before execution and report the missing gate or guard evidence.
