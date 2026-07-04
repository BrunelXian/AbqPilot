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
