# ACOM Mode

ACOM means AbqPilot Codex Operator Mode.

ACOM is the default practical execution direction for Codex-assisted work. AbqPilot generates bounded Codex handoff packages, Codex CLI may be used externally by a human operator, and AbqPilot later intakes structured artifacts for deterministic validation.

Codex is an external operator, not the final evidence authority. Codex natural-language summaries are supporting notes only. They are not final evidence.

AbqPilot remains the planner, validator, and evidence authority. Returned artifacts must be validated through schemas, file hashes, safety flags, tests, StaticValidator, DiffGuard, PhysicsGuard, MCPGuard when model conditions or INP patches may be affected, Job/ODB diagnosis where applicable, and safety/secret audits.

Stage 5.0A implements infrastructure only. It does not call Codex CLI, does not run solver, does not enqueue jobs, and does not open ODB files.
## Stage 5.0B Pipeline Context

ACOMAgent is a support agent in the pipeline-style architecture. It generates and validates Codex handoff packages, intakes structured result files, rejects unsafe safety flags, and marks outputs as pending AbqPilot revalidation.

ACOM is not the main scheduler and does not call Codex CLI automatically. Codex/LLM summary is not final evidence. ACOM outputs must return through the normal RUN/HANDOFF/GATE evidence protocol and deterministic validators before any evidence claim.

## Stage 5.0C Templates

Stage 5.0C adds real ACOM templates on the pipeline protocol. A template handoff creates `trace/RUN_XXX_ACOM_<TEMPLATE_ID>.md`, `handoffs/HANDOFF_XXX_ACOM_TO_CODEX_OPERATOR.md`, and `codex_handoff/`. High-risk or model-condition templates can also create a pending revalidation gate. Codex still executes externally and manually; AbqPilot does not call Codex CLI, Codex summaries are not final evidence, and AbqPilot revalidation is required.

## Stage 5.0D Result Intake

ACOM result intake reads the generated `codex_handoff/handoff_manifest.json` and a returned `codex_result/structured_result.json`. It validates schema, safety flags, task identity, handoff identity, and declared artifact existence. Accepted intake is recorded as `ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION` and routed to a downstream AbqPilot agent. It is not final evidence and does not approve solver execution, ODB metrics, or evidence freeze.
