# CandidateBuilderAgent Input Contract

## What the agent may receive
- Audit handoff and findings.
- Target change definition.
- Source artifact references and approved output root.

## Required upstream handoff
`handoffs/HANDOFF_002_AUDIT_TO_CANDIDATE_BUILDER.md`

## Required artifacts
- Audit report.
- Source model artifacts when candidate generation is allowed.

## Required frontmatter fields
The upstream handoff must define `task_id`, `from_agent`, `to_agent`, `from_run`, `target_run`, `risk_level`, and `expected_output`.

## Input validation obligations
Confirm candidate work is allowed, target change is bounded, and source artifacts remain immutable.

## Missing-input behavior
Stop and document missing target, source, or output contract.
