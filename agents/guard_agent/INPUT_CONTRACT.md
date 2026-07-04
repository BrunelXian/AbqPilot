# GuardAgent Input Contract

## What the agent may receive
- Candidate build handoff.
- Candidate and source artifact paths.
- Target change and forbidden scope.

## Required upstream handoff
`handoffs/HANDOFF_003_CANDIDATE_BUILDER_TO_GUARD.md`

## Required artifacts
- Candidate artifact.
- Source artifact.
- Target change declaration.

## Required frontmatter fields
The upstream handoff must include `doc_type`, `task_id`, `handoff_id`, `from_agent`, `to_agent`, `from_run`, `target_run`, `risk_level`, and `expected_output`.

## Input validation obligations
Confirm source and candidate paths exist and are distinct; validate original model-condition preservation, not only target edits.

## Missing-input behavior
Stop and issue guarded ineligibility until missing evidence is provided.
