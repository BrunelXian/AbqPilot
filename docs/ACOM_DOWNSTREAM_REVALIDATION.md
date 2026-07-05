# ACOM Downstream Revalidation

Stage 5.0E lets downstream revalidation agents catch accepted ACOM results.

It creates revalidation scaffolds only. It does not automatically execute downstream agents. It does not approve evidence. Codex summary is not final evidence.

The flow is:

```text
ACOMAgent
-> accepted pending revalidation result
-> downstream revalidation package
-> downstream RUN scaffold
-> pending GATE
-> handoff to PipelineSupervisor or next appropriate agent
```

Supported downstream agents include GuardAgent, DocsStatusAgent, SoftwareQAAgent, DiagnosisAgent, AuditAgent, EvidenceReportAgent, PipelineSupervisor, and CandidateBuilderAgent.

The gate decision remains `PENDING_REVALIDATION`, never `APPROVED`.

Stage 5.0F executes deterministic non-solver revalidation only for DocsStatusAgent, SoftwareQAAgent, AuditAgent, EvidenceReportAgent, and PipelineSupervisor. GuardAgent, CandidateBuilderAgent, DiagnosisAgent, ExecutionAgent, and MetricsAgent are blocked in Stage 5.0F.

`NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR` means the low-risk checks passed and may be reviewed by PipelineSupervisor. It is not final evidence accepted.

Stage 5.0G adds the PipelineSupervisor review gate for completed non-solver revalidation results. Accepted means accepted for `NON_SOLVER_EVIDENCE_LEDGER` only; final evidence remains separate and unapproved.

Stage 5.0H adds EvidenceReportAgent non-solver summary reporting. It summarizes `NON_SOLVER_EVIDENCE_LEDGER` and returns a pending supervisor acknowledgement gate; it does not update the final evidence ledger.

Stage 5.0I lets PipelineSupervisor acknowledge that summary and hand off to DocsStatusAgent for non-final status synchronization. It does not approve final evidence or update the final evidence ledger.
## Stage 5.1A GUI View

Stage 5.1A lets the GUI display downstream revalidation scaffold state from task workspace records. This is read-only workflow interpretation plus safe action grouping. It does not execute high-risk downstream agents, run Codex, run solver, open ODB, enqueue jobs, or approve evidence.
