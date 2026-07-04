# PipelineSupervisor Non-Solver Review

Stage 5.0G lets PipelineSupervisor review completed Stage 5.0F non-solver revalidation results.

Accepted means accepted for the non-solver evidence ledger only.

It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

Supported source results are:

- `NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR`
- `NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR`

Blocked source results include failed or blocked revalidation, high-risk agents, unsupported agents, unsafe flags, automatic execution, and any attempt to claim final evidence approval.

Accepted review writes:

- `supervisor_review/SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json`
- `supervisor_review/SUPERVISOR_NON_SOLVER_REVIEW_REPORT.md`
- `trace/RUN_XXX_PIPELINE_SUPERVISOR_NON_SOLVER_REVIEW.md`
- `gates/GATE_XXX_SUPERVISOR_NON_SOLVER_REVIEW.md`
- `handoffs/HANDOFF_XXX_SUPERVISOR_NON_SOLVER_REVIEW_TO_EVIDENCE_REPORT_AGENT.md`
- `NON_SOLVER_EVIDENCE_LEDGER.md`
- `NON_SOLVER_EVIDENCE_LEDGER.json`

The final evidence ledger remains separate from the non-solver evidence ledger.

Accepted gate decisions are:

- `ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER`
- `ACCEPTED_WITH_WARNINGS_FOR_NON_SOLVER_EVIDENCE_LEDGER`

Blocked decisions use:

- `BLOCKED`

The supervisor review gate never uses `APPROVED`.
