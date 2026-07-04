# ACOM Pipeline Integration

Stage 5.0C connects ACOM handoff infrastructure to the Stage 5.0B pipeline protocol. ACOMAgent is a support agent. It may generate bounded Codex handoff packages, validate packages, intake `structured_result.json`, reject unsafe safety flags, mark results as pending AbqPilot revalidation, and create RUN/HANDOFF records describing the ACOM step.

## Generated Structure

For a pipeline task under `runs/tasks/<task_id>/`, an ACOM template handoff creates or updates:

```text
trace/RUN_XXX_ACOM_<TEMPLATE_ID>.md
handoffs/HANDOFF_XXX_ACOM_TO_CODEX_OPERATOR.md
gates/GATE_XXX_PENDING_ACOM_RESULT_REVALIDATION.md when required
codex_handoff/
codex_result/
artifacts/
```

The generated `codex_handoff/` package includes `codex_task.md`, input/allowed/forbidden manifests, expected outputs, evidence contract, output schema, safety contract, acceptance criteria, and handoff manifest.

## Safety Boundary

ACOM templates do not auto-call Codex, do not run solver, do not launch QueueRunner, do not launch abqjobpilot GUI, do not enqueue jobs, do not open ODB files, do not mutate source CAE/INP/ODB files, and do not bypass validators, MCPGuard, diagnosis, gates, or human approvals.

Codex summaries are not final evidence. AbqPilot revalidation is required before downstream evidence or PASS claims.

## Stage 5.0D Result Return Path

Stage 5.0D adds the return path from `codex_result/structured_result.json` to pipeline revalidation. ACOMAgent writes `codex_result/acom_result_intake.json`, `trace/RUN_XXX_ACOM_RESULT_INTAKE.md`, `gates/GATE_XXX_ACOM_RESULT_REVALIDATION.md`, and a downstream `HANDOFF_XXX_ACOM_RESULT_TO_<DOWNSTREAM_AGENT>.md`.

Accepted intake means accepted for AbqPilot revalidation, not accepted as evidence. Unsafe safety flags, task mismatch, handoff mismatch, missing handoff, missing result, and missing claimed artifacts are rejected or blocked. No Codex CLI call, solver run, queue action, ODB open, or automatic downstream scheduling is performed.
