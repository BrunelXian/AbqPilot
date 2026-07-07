# Execution Modes

AbqPilot-v2 supports two documented execution directions.

## ACOM

ACOM is AbqPilot Codex Operator Mode. It is the default practical mode.

The chain is:

```text
AbqPilot planner -> bounded Codex handoff -> external Codex operator -> structured artifacts -> AbqPilot validation
```

AbqPilot does not automatically call Codex CLI in Stage 5.0A. Codex summaries are not final evidence.

## NARM

NARM is Native Agent Runtime Mode. It is optional and advanced.

The chain is:

```text
AbqPilot native runtime -> deterministic tool execution -> AbqPilot validation
```

Both modes must satisfy the same evidence and safety contracts. MCPGuard is required when model conditions or INP patches may be affected.

Stage 5.0E keeps ACOM pipeline-style: accepted ACOM results route into downstream revalidation scaffolds, not automatic execution. Codex summary is not final evidence, and downstream revalidation gates remain pending until deterministic AbqPilot checks occur.
## Stage 5.0B Pipeline Protocol Mode

Pipeline protocol mode is a documentation, scaffold, and validation layer. It defines bounded pipeline stations, flat `RUN_XXX.md` trace files, `HANDOFF_XXX.md` input contracts, and `GATE_XXX.md` high-risk decisions.

This mode does not add automatic agent scheduling, LangGraph, Agents SDK, Codex runtime bridge, generic subprocess launcher, solver execution, QueueRunner launch, enqueue, direct ODB open, or metrics extraction. PipelineSupervisor observes, gates, and freezes; it is not a central dispatcher for every low-risk transition.

## ACOM Template Mode

Stage 5.0C ACOM template mode generates bounded Codex handoff packages within the pipeline protocol. Codex remains an external manual operator. AbqPilot does not call Codex CLI, and returned Codex summaries are not final evidence.

Stage 5.0D ACOM result intake is also non-executing. It reads structured results, rejects unsafe returns, writes pipeline revalidation records, and routes the result to a downstream AbqPilot agent. It does not invoke Codex, schedule agents, run solver, enqueue jobs, open ODB files, or freeze final evidence.

Stage 5.0F remains non-solver and non-ODB. It executes deterministic revalidation only for DocsStatusAgent, SoftwareQAAgent, AuditAgent, EvidenceReportAgent, and PipelineSupervisor after an explicit CLI/GUI call. GuardAgent, CandidateBuilderAgent, DiagnosisAgent, ExecutionAgent, and MetricsAgent are blocked until later guarded stages.

Stage 5.0G lets PipelineSupervisor review Stage 5.0F results and update the non-final non-solver evidence ledger. This is not final evidence freeze and does not approve solver, ODB, metrics, or model mutation.

Stage 5.0H lets EvidenceReportAgent summarize the non-final non-solver ledger. This remains an ACOM pipeline evidence-reporting step only; it does not call Codex CLI, run solver, open ODB, auto-schedule agents, update the final evidence ledger, or freeze a verdict.

Stage 5.0I lets PipelineSupervisor acknowledge the non-final non-solver summary. This remains a pipeline recordkeeping step only; it does not call Codex CLI, run solver, open ODB, auto-schedule agents, update the final evidence ledger, or freeze a verdict.

Stage 5.1A presents the ACOM/non-solver workflow in the GUI as information architecture and safe UX only. It does not add a new execution mode. ACOM remains external-operator mode, NARM remains optional, and the GUI does not call Codex CLI, run solver, open ODB, queue jobs, auto-schedule agents, approve final evidence, or freeze final verdict.

Stage 5.1B keeps the same execution-mode boundary and improves only the GUI visual layout/readability. It does not add native runtime execution, automatic Codex execution, automatic scheduling, solver execution, ODB access, queue submission, final evidence approval, or final verdict freeze.

Stage 5.1C keeps ACOM and NARM boundaries unchanged. Timeline interaction is read-only evidence navigation and does not execute Codex, native agents, solver, ODB, queue, scheduling, final evidence approval, or final verdict freeze.

Stage 5.1D also keeps execution modes unchanged. Report and artifact preview is read-only presentation over existing records; it does not launch external editors, execute file contents, call Codex CLI, run solver, open ODB, queue jobs, schedule agents, approve final evidence, update the final evidence ledger, or freeze verdict.

Stage 5.1E keeps execution modes unchanged. Guided recommendation is advisory view-model generation only. It may tell the user which existing safe panel action is appropriate, but it does not call Codex CLI, execute NARM workflows, schedule agents, run solver, open ODB, queue jobs, approve final evidence, or freeze verdict.

Stage 5.1F keeps execution modes unchanged. GUI beta readiness smoke is a non-final validation report for the GUI cockpit; it does not execute ACOM, NARM, solver, ODB, queue, scheduling, final evidence approval, or final verdict freeze.

Stage 5.2A also keeps execution modes unchanged. High-risk gate UX records are specification-only previews and do not create real approving gates, mutate task `gates/`, update `TASK_FINAL_EVIDENCE_LEDGER.md`, call Codex CLI, run solver, open ODB, queue jobs, schedule agents, approve final evidence, or freeze verdict.

Stage 5.2B keeps execution modes unchanged as well. Controlled solver approval token validation is preview-only; future real approval and future solver execution must remain separate stages, and ODB/metrics/final evidence remain separately gated.

Stage 5.2C also keeps execution modes unchanged. The inactive controlled solver human gate draft is not active approval and not execution. It may define expected future shapes, but those shapes are not written as active task gates or executable handoffs.

Stage 5.2D keeps execution modes unchanged. Active controlled solver human gate records are defined only as schema, validation, token-consumption, candidate-hash, disabled-writer, GUI-card, and report design objects. Stage 5.2D does not call Codex CLI, run solver, create solver requests, write real active task gates, write active execution handoffs, open ODB, approve metrics, approve final evidence, or freeze verdict.

Stage 5.2E also keeps execution modes unchanged. Fixture-only active gate writer verification can write test fixture gate records only. It does not write real task gates, create solver requests, run solver, open ODB, approve metrics, approve final evidence, or freeze verdict.

Stage 5.2F creates one real human approval gate under the dedicated smoke task only. This does not change execution modes: solver execution is still not allowed, no solver request is created, no ODB or metrics authority is granted, and final evidence remains locked.

Stage 5.2G creates a controlled solver execution handoff draft only in non-active draft/report locations. It does not create active `HANDOFF_*.md` execution records, solver request files, solver execution, queue mutation, ODB, metrics, final evidence, or verdict freeze.

Stage 5.2H creates controlled solver request draft schema artifacts only in non-active draft/report locations. It does not create active `solver_request.json`, `job_request.json`, `abaqus_job.json`, solver launchers, active execution handoffs, solver execution, queue mutation, ODB, metrics, final evidence, or verdict freeze.

Stage 5.2I validates the controlled solver request draft as a preflight-only report. It does not create active request files, output execution directories, solver launchers, active execution handoffs, solver execution, queue mutation, ODB, metrics, final evidence, or verdict freeze.

Stage 5.2J materializes a dry-run-only controlled solver request artifact. It does not create active `solver_request.json`, `job_request.json`, or `abaqus_job.json`, does not create output execution directories, does not call Abaqus, does not run solver, does not queue jobs, does not open ODB, and does not approve metrics, final evidence, or verdict.

Stage 5.3A-v2 adds one fixed controlled Abaqus demo smoke corridor after workspace guard remediation. It can attempt the fixed Abaqus command for a copied demo INP only and capture status; it does not generalize solver execution, open ODB, extract metrics, queue jobs, approve final evidence, or freeze verdict.
