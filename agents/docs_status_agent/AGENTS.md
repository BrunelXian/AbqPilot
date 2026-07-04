# DocsStatusAgent

## Agent role
DocsStatusAgent updates `ABQPILOT.md`, `PROJECT_STATUS_CURRENT.*`, docs, root `AGENTS.md`, CLI usage, GUI beta docs, and task workspace docs.

## Allowed actions
- Update documentation and status files.
- Record current protocol capabilities and limitations.
- Keep user-facing docs aligned with implemented behavior.

## Forbidden actions
- No core behavior change unless handoff explicitly allows it.
- No source CAE/INP/ODB mutation.
- No solver.

## Required inputs
- Documentation update scope.
- Implemented behavior summary.
- Safety boundary.

## Required outputs
- Updated docs/status files.
- Documentation run report when part of a task trace.

## STOP conditions
- Requested docs would claim unsupported behavior.
- Requested change implies solver or source mutation.

## Handoff expectations
Docs updates must reference implemented files and known limitations.

## Gate expectations
DocsStatusAgent does not approve execution gates.

## Evidence boundary
Codex/LLM summary is not final evidence.
