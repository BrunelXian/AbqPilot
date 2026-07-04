# ACOM Result Pipeline Revalidation

Stage 5.0D implements the return path from an external Codex operator back into the AbqPilot pipeline protocol:

```text
codex_result/structured_result.json
-> ACOMAgent result intake
-> trace/RUN_XXX_ACOM_RESULT_INTAKE.md
-> gates/GATE_XXX_ACOM_RESULT_REVALIDATION.md
-> handoffs/HANDOFF_XXX_ACOM_RESULT_TO_<DOWNSTREAM_AGENT>.md
```

ACOM result intake is a structural and safety classification step only. `ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION` means the returned structured result is safe enough to hand to a deterministic AbqPilot agent for revalidation. It is not accepted as final evidence, and it does not approve solver execution, ODB metrics, or final PASS evidence.

## Intake Status Values

- `ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION`
- `ACOM_RESULT_REJECTED_SCHEMA_INVALID`
- `ACOM_RESULT_REJECTED_SAFETY_FLAGS`
- `ACOM_RESULT_REJECTED_TASK_MISMATCH`
- `ACOM_RESULT_REJECTED_HANDOFF_MISMATCH`
- `ACOM_RESULT_BLOCKED_MISSING_RESULT`
- `ACOM_RESULT_BLOCKED_MISSING_HANDOFF`
- `ACOM_RESULT_BLOCKED_MISSING_ARTIFACTS`
- `ACOM_RESULT_REVIEW_REQUIRED`

## Safety Rejection

Intake rejects a result if any forbidden safety flag is true, including solver start, QueueRunner launch, abqjobpilot GUI launch, direct ODB open, `.env` read, source sanity-base mutation, `shell=True`, generic subprocess addition, automatic Codex CLI call, fabricated human approval, Codex-generated approval token, or direct final evidence freeze.

## Routing

Routing is based on `template_id` or legacy task type. Examples:

- `mcpguard_review` routes to `GuardAgent`.
- `docs_status_update` routes to `DocsStatusAgent`.
- `test_expansion` and `safety_secret_audit` route to `SoftwareQAAgent`.
- `job_odb_diagnosis_review` and `abqjobpilot_record_audit` route to `DiagnosisAgent`.
- `stage_implementation` routes to `SoftwareQAAgent` with `DocsStatusAgent` recorded as an additional downstream reviewer.

The route is recorded in `codex_result/acom_result_intake.json` and in the downstream handoff. No downstream agent is automatically invoked.

## Gate Boundary

Accepted intake creates a revalidation gate with:

```text
decision: PENDING_REVALIDATION
codex_summary_is_final_evidence: false
abqpilot_revalidation_required: true
```

Rejected or blocked intake creates a blocked gate or blocked record. ACOMAgent never writes an approved evidence gate for Codex output.
