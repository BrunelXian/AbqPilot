# Codex Result Intake

ACOM result intake expects a structured result JSON:

```text
runs/tasks/<task_id>/codex_result/structured_result.json
```

The result must include file changes, commands run, tests run, artifacts, safety flags, validation claims, final status, and known limitations.

Unsafe safety flags cause rejection. Stage 5.0A rejects results claiming solver start, QueueRunner launch, abqjobpilot GUI launch, ODB direct open, `.env` read, forbidden path touch, source sanity-base mutation, `shell=True`, generic subprocess addition, or automatic Codex CLI call.

For Stage 5.0C template handoffs, intake remains pending AbqPilot revalidation. Codex natural-language summaries are not final evidence. Model-condition and INP-patch templates must return MCPGuard-compatible evidence or a documented not-applicable reason before downstream guards can proceed.

A safe placeholder result is accepted only as:

```text
ACOM_RESULT_SCHEMA_ACCEPTED_PENDING_ABQPILOT_REVALIDATION
```

AbqPilot deterministic revalidation is still required. Codex natural-language summaries are not final evidence.

## Stage 5.0D Pipeline Revalidation Gate

Pipeline-integrated ACOM result intake now creates a structured intake artifact, a RUN record, a revalidation GATE, and a downstream handoff. The accepted status is `ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION`; it means only that the result is structurally safe enough for deterministic AbqPilot revalidation.

Unsafe flags such as `solver_started`, `queue_runner_launched`, `abqjobpilot_gui_launched`, `odb_opened`, `env_read`, `forbidden_path_touched`, `source_sanity_base_mutated`, `shell_true_used`, `generic_subprocess_added`, `codex_cli_auto_called`, `final_evidence_frozen`, `human_approval_fabricated`, and `approval_token_generated_by_codex` cause rejection. Accepted intake creates `decision: PENDING_REVALIDATION`, not an approved evidence gate.
