# ACOMAgent Input Contract

## What the agent may receive
- Codex handoff request.
- Codex structured result placeholder.
- Safety boundary and allowed artifact paths.

## Required upstream handoff
Support-agent handoff or human request defining ACOM scope.

## Required artifacts
- Handoff directory or structured result file.

## Required frontmatter fields
When attached to pipeline tasks, referenced RUN/HANDOFF files must keep standard frontmatter.

## Input validation obligations
Reject unsafe safety flags, missing scope, automatic Codex execution, and final-evidence claims.

## Missing-input behavior
Stop and report `ACOM_INPUT_INCOMPLETE`.
