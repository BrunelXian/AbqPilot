# GUI Information Architecture

Stage 5.1A reorganizes the GUI around safe workflow state rather than a flat button dump.

The GUI sections are:

- Project Status
- Task Workspace
- Pipeline Trace
- ACOM Handoff
- ACOM Result Intake
- Downstream Revalidation
- Non-Solver Revalidation Execution
- PipelineSupervisor Review
- EvidenceReportAgent Non-Solver Summary
- PipelineSupervisor Summary Ack
- Safety / Audit Status
- Disabled High-Risk Actions

The workflow state model reads task workspace records and classifies ACOM/non-solver progress through the RUN/HANDOFF/GATE protocol. It does not run solver, open ODB, call Codex CLI, enqueue jobs, auto-schedule agents, approve final evidence, or freeze final verdict.

The GUI must clearly display:

- Non-final / non-solver record
- Final evidence remains locked
- Solver, ODB, metrics, and model mutation are disabled in this stage
- Codex results require AbqPilot revalidation
- Supervisor acknowledgement does not freeze final verdict
- High-risk agents are intentionally blocked

Stage 5.1A does not update `TASK_FINAL_EVIDENCE_LEDGER.md`.

## Stage 5.1B Visual Polish

Stage 5.1B improves GUI layout and readability without adding execution capability. It adds status cards, a workflow timeline, readable badges, action panels, and disabled high-risk action summaries using the Stage 5.1A workflow state and safe action catalog as source of truth.

The visual polish must not weaken safety boundaries. It does not run solver, open ODB, call Codex CLI, launch QueueRunner, queue jobs, auto-schedule agents, approve final evidence, or freeze final verdict.

Stage 5.1D adds read-only Markdown and JSON artifact preview models to this information architecture. The previewer flags unsafe approval claims but does not fix or mutate files, launch external editors, execute commands, or update the final evidence ledger.

Stage 5.1E adds deterministic guided next-step recommendation on top of the same workflow state and safe action catalog. Recommendations point to existing safe panels and remain advisory; they do not run Codex CLI, solver, ODB, queue, scheduling, high-risk agents, final evidence approval, or final verdict freeze.

Stage 5.1F validates the GUI information architecture with an end-to-end non-solver safe workflow smoke. GUI beta readiness remains non-final and does not update the final evidence ledger.

## Stage 5.1C Trace Viewer

Stage 5.1C adds read-only timeline interaction. Selecting a timeline node resolves related RUN/HANDOFF/GATE records, ledgers, reports, and JSON artifacts for inspection. It does not run agents or mutate artifacts.
