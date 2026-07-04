# Codex Handoff Contract

Stage 5.0A defines bounded ACOM handoff packages under:

```text
runs/tasks/<task_id>/codex_handoff/
```

Required files:

- `codex_task.md`
- `input_manifest.json`
- `allowed_paths.json`
- `forbidden_paths.json`
- `allowed_commands.json`
- `forbidden_commands.json`
- `expected_outputs.json`
- `evidence_contract.json`
- `output_contract.schema.json`
- `safety_contract.json`
- `acceptance_criteria.md`
- `handoff_manifest.json`

Every handoff forbids solver launch, QueueRunner launch, abqjobpilot GUI launch, enqueue, ODB direct open, `.env` reads, source sanity-base mutation, arbitrary raw INP edits, `shell=True`, generic subprocess launchers, LangGraph, Agents SDK, Codex runtime bridges, and automatic Codex CLI calls from AbqPilot.

Stage 5.0C ACOM templates must be generated as part of the pipeline protocol. A generated handoff must include pipeline RUN/HANDOFF records, the `codex_handoff/` package, and evidence contracts that state Codex summaries are not final evidence and AbqPilot revalidation is required. Isolated Codex prompts without pipeline trace are not accepted.

Stage 5.0D requires returned Codex artifacts to enter through `intake-codex-result`. The returned `structured_result.json` must match the handoff task ID and handoff ID, keep unsafe safety flags false, and declare artifacts that exist. Intake output is routed for AbqPilot revalidation and is not final evidence.

Codex may only act as an external bounded operator. AbqPilot validates returned artifacts.
