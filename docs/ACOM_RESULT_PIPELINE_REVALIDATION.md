# ACOM Result Pipeline Revalidation

ACOM result intake accepts structured Codex output only as input for deterministic AbqPilot revalidation.

`ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION` does not mean evidence accepted, solver approved, ODB accepted, metrics accepted, or final verdict frozen.

It is not accepted as final evidence.

Unsafe safety flags cause rejection before any downstream revalidation scaffold is created.

Stage 5.0E creates downstream revalidation packages under:

```text
runs/tasks/<task_id>/revalidation/<downstream_agent>_<id>/
```

The generated package includes plan, inputs, checklist, expected outputs, scaffold JSON, and scaffold report.

Stage 5.0F can execute non-solver deterministic revalidation on those packages. Supported agents are DocsStatusAgent, SoftwareQAAgent, AuditAgent, EvidenceReportAgent, and PipelineSupervisor. High-risk agents remain blocked. Generated result gates are `PENDING_SUPERVISOR_REVIEW` or `BLOCKED`, never `APPROVED`.

Stage 5.0G lets PipelineSupervisor convert accepted non-solver revalidation into a non-final `NON_SOLVER_EVIDENCE_LEDGER` entry. This does not freeze the final evidence ledger.

Stage 5.0H lets EvidenceReportAgent summarize that non-final non-solver ledger and write a pending supervisor acknowledgement gate. The summary does not update `TASK_FINAL_EVIDENCE_LEDGER.md`, approve solver, approve ODB, approve metrics, or freeze final verdict.

Stage 5.0I lets PipelineSupervisor acknowledge the EvidenceReportAgent summary as a non-final project record. The acknowledgement writes `NON_SOLVER_SUMMARY_ACK_LEDGER.md/json` only and does not update `TASK_FINAL_EVIDENCE_LEDGER.md`.
## Stage 5.1A GUI View

Stage 5.1A displays ACOM result intake state in the GUI as pending or accepted-pending-revalidation. Codex natural-language summaries remain non-evidence, Codex CLI is not called, and accepted intake still requires deterministic AbqPilot revalidation before any evidence claim.
