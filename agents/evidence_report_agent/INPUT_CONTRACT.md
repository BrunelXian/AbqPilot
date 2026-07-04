# EvidenceReportAgent Input Contract

## What the agent may receive
- Metrics handoff.
- Full task trace, handoff, and gate set.
- Validator, diagnosis, metrics, and report artifacts.

## Required upstream handoff
`handoffs/HANDOFF_007_METRICS_TO_EVIDENCE_REPORT.md` when metrics exist.

## Required artifacts
- Trace index.
- RUN, HANDOFF, and GATE files.
- Evidence artifacts for any claim.

## Required frontmatter fields
All key Markdown files must include `doc_type`, `task_id`, and type-specific required keys.

## Input validation obligations
Validate trace completeness, artifact references, known limitations, and claim boundary.

## Missing-input behavior
Stop or recommend WARNING/FAIL rather than fabricating final evidence.
