# PipelineSupervisor Input Contract

## What the agent may receive
- Trace index files.
- RUN, HANDOFF, and GATE Markdown with YAML frontmatter.
- Final evidence ledgers and artifact references.

## Required upstream handoff
No single upstream handoff is required; the supervisor observes the full task trace.

## Required artifacts
- `TRACE_INDEX.md`
- Relevant `trace/RUN_XXX.md`
- Relevant `handoffs/HANDOFF_XXX.md`
- Relevant `gates/GATE_XXX.md`

## Required frontmatter fields
- RUN: `doc_type`, `task_id`, `run_id`, `agent`, `status`, `risk_level`, `forbidden_actions`
- HANDOFF: `doc_type`, `task_id`, `handoff_id`, `from_agent`, `to_agent`, `from_run`, `target_run`
- GATE: `doc_type`, `task_id`, `gate_id`, `transition`, `decision`, `approver_type`

## Input validation obligations
Confirm all referenced files exist, frontmatter is present, and high-risk gates are approved before risky transitions.

## Missing-input behavior
Stop and report the missing input. Do not infer final evidence from narrative summaries.
