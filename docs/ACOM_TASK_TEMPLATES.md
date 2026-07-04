# ACOM Task Templates

Stage 5.0C adds real ACOM templates on top of the pipeline protocol. ACOM templates generate pipeline `RUN_XXX.md` and `HANDOFF_XXX.md` records plus a bounded `codex_handoff/` package. Codex still executes externally and manually. AbqPilot does not call Codex CLI, and Codex summaries are not final evidence.

## Registered Templates

- `stage_implementation`
- `read_only_audit`
- `guarded_candidate_preview`
- `controlled_execution_planning`
- `job_odb_diagnosis_review`
- `mcpguard_review`
- `abqjobpilot_record_audit`
- `docs_status_update`
- `test_expansion`
- `safety_secret_audit`

High-risk execution templates are not enabled: automatic solver run, automatic solver retry, automatic queue enqueue, automatic Codex execution, direct ODB metrics extraction, source CAE mutation, and source INP mutation are not registered.

## Evidence Contract

Each template requires `structured_result.json`, file hashes, tests result where applicable, safety flags, and AbqPilot revalidation. Codex natural-language summary is not final evidence. Model-condition or INP-patch related templates require MCPGuard, target patch isolation, and original-condition preservation checks.

## Result Intake

Stage 5.0D connects template output back to the pipeline. A returned `structured_result.json` is intaken by ACOMAgent, classified, and routed to the deterministic downstream AbqPilot agent. The intake writes RUN/HANDOFF/GATE records and preserves `abqpilot_revalidation_required=true`. Template output never becomes final evidence directly.

## CLI

```powershell
python -m abqpilot.cli list-acom-templates
python -m abqpilot.cli describe-acom-template --template-id mcpguard_review
python -m abqpilot.cli generate-codex-handoff --task-id <task_id> --template-id mcpguard_review
python -m abqpilot.cli validate-acom-template-pack
```
