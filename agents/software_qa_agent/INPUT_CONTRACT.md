# SoftwareQAAgent Input Contract

## What the agent may receive
- Test scope.
- Safety audit queries.
- Changed file list.

## Required upstream handoff
Support handoff or human QA request.

## Required artifacts
- Source tree paths.
- Expected test baseline.

## Required frontmatter fields
If part of a task trace, QA RUN must use `doc_type: run_report`.

## Input validation obligations
Confirm QA commands are safe and do not launch high-risk workflows.

## Missing-input behavior
Stop or run only the safe subset that can be justified.
