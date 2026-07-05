# ACOM Non-Solver Revalidation

Stage 5.0F adds deterministic revalidation execution for low-risk ACOM downstream scaffolds.

Supported agents:

- DocsStatusAgent
- SoftwareQAAgent
- AuditAgent
- EvidenceReportAgent
- PipelineSupervisor

Blocked high-risk agents:

- GuardAgent
- CandidateBuilderAgent
- DiagnosisAgent
- ExecutionAgent
- MetricsAgent

Stage 5.0F reads an existing `revalidation/<Agent>_<id>/REVALIDATION_SCAFFOLD.json`, the ACOM intake artifact, and the Codex `structured_result.json` when available. It writes `REVALIDATION_EXECUTION_RESULT.json`, `REVALIDATION_EXECUTION_REPORT.md`, and for supported agents a flat RUN/GATE/HANDOFF result set.

This is not automatic scheduling. The executor only runs when explicitly invoked through CLI or GUI.

No solver, ODB, queue, Codex CLI, LLM provider, high-risk downstream agent, automatic scheduling, or evidence approval occurs.

A pass status means:

```text
NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR
```

It means the low-risk deterministic checks passed and may be reviewed by PipelineSupervisor. It does not mean final evidence accepted, solver approved, ODB accepted, metrics accepted, or final verdict frozen.

It is not final evidence accepted.

Supported result gates use:

```text
PENDING_SUPERVISOR_REVIEW
```

Failed or blocked results use:

```text
BLOCKED
```

They never use `APPROVED`.

Stage 5.0G lets PipelineSupervisor review completed Stage 5.0F results. Accepted review writes `NON_SOLVER_EVIDENCE_LEDGER.md/json` only. It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

Stage 5.0H lets EvidenceReportAgent summarize `NON_SOLVER_EVIDENCE_LEDGER.md/json` into a non-final non-solver evidence report. It does not update `TASK_FINAL_EVIDENCE_LEDGER.md` and does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.

Stage 5.0I lets PipelineSupervisor acknowledge the non-solver summary into `NON_SOLVER_SUMMARY_ACK_LEDGER.md/json`. It remains non-final and does not update `TASK_FINAL_EVIDENCE_LEDGER.md`.
## Stage 5.1A GUI View

Stage 5.1A groups ACOM and non-solver revalidation actions in the GUI by workflow stage. It displays non-solver revalidation, PipelineSupervisor review, EvidenceReportAgent summary, and PipelineSupervisor acknowledgement state as non-final project records only.

High-risk agents remain blocked in the GUI. Solver, ODB, metrics, queue, Codex execution, automatic scheduling, final evidence approval, and final verdict freeze controls are disabled.
