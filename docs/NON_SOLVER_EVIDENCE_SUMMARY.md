# Non-Solver Evidence Summary

Stage 5.0H lets EvidenceReportAgent summarize `NON_SOLVER_EVIDENCE_LEDGER.md/json`.

The summary is non-final and non-solver only. It does not update `TASK_FINAL_EVIDENCE_LEDGER.md`.
It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.
It preserves the pipeline RUN/HANDOFF/GATE protocol.

## Inputs

- `NON_SOLVER_EVIDENCE_LEDGER.json`
- `NON_SOLVER_EVIDENCE_LEDGER.md`
- Pipeline RUN/HANDOFF/GATE records
- Supervisor review artifacts when available
- Non-solver revalidation artifacts when available
- ACOM result intake artifacts when available

## Outputs

- `evidence_report/NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json`
- `evidence_report/NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md`
- `trace/RUN_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md`
- `gates/GATE_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md`
- `handoffs/HANDOFF_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY_TO_PIPELINE_SUPERVISOR.md`

The gate decision is `NON_SOLVER_SUMMARY_READY_PENDING_SUPERVISOR_ACK`,
`NON_SOLVER_SUMMARY_READY_WITH_WARNINGS_PENDING_SUPERVISOR_ACK`, or `BLOCKED`.
It is never `APPROVED`.

## Claim Boundary

EvidenceReportAgent may summarize accepted non-solver ledger entries. That summary does not become final
evidence. It does not freeze final verdicts and does not authorize solver execution, ODB intake, metrics,
model mutation, Codex execution, or automatic downstream scheduling.

Stage 5.0I lets PipelineSupervisor acknowledge this summary into `NON_SOLVER_SUMMARY_ACK_LEDGER`.
The acknowledgement remains non-final and non-solver only, and it must not update `TASK_FINAL_EVIDENCE_LEDGER.md`.
