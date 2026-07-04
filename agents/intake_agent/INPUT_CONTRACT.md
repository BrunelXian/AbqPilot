# IntakeAgent Input Contract

## What the agent may receive
- Human task objective.
- Candidate input paths and status statements.
- Risk-level hints.

## Required upstream handoff
None. IntakeAgent starts the task trace.

## Required artifacts
- Human-readable task request.
- Workspace root.

## Required frontmatter fields
Output frontmatter must include `doc_type`, `task_id`, `run_id`, `agent`, `status`, `risk_level`, and `forbidden_actions`.

## Input validation obligations
Confirm task id, objective, and input path intent before creating the task scaffold.

## Missing-input behavior
Stop with a missing-input note in `RUN_001_INTAKE.md` if the objective or task id is unavailable.
