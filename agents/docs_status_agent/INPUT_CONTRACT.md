# DocsStatusAgent Input Contract

## What the agent may receive
- Implemented behavior summary.
- List of changed files.
- Required status verdict wording.

## Required upstream handoff
Support handoff or human docs request.

## Required artifacts
- Source files, test outputs, or reports supporting documentation claims.

## Required frontmatter fields
If part of a pipeline task, docs RUN must include `doc_type`, `task_id`, `run_id`, `agent`, and `status`.

## Input validation obligations
Confirm docs only claim implemented and tested behavior.

## Missing-input behavior
Stop or mark documentation claim as pending evidence.
