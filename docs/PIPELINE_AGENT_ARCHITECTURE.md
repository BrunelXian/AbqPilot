# Pipeline Agent Architecture

AbqPilot uses a pipeline-style multi-agent architecture, not a hierarchical organization.

The main execution flow is linear:

```text
PipelineSupervisor observes / gates / freezes

IntakeAgent
-> AuditAgent
-> CandidateBuilderAgent
-> GuardAgent
-> ExecutionAgent
-> DiagnosisAgent
-> MetricsAgent
-> EvidenceReportAgent
```

Support agents are:

```text
ACOMAgent
SoftwareQAAgent
DocsStatusAgent
```

## Core Rules

- Agent means bounded pipeline station.
- HANDOFF means station-to-station input contract.
- RUN_XXX.md means execution trace plus supervisor step report.
- GATE_XXX.md means high-risk transition decision.
- PipelineSupervisor observes, gates, and freezes. It is not a central dispatcher for every low-risk transition.
- ACOM remains a support agent pathway. It can package or validate Codex handoffs but cannot provide final evidence alone.

## Safety Boundary

This architecture does not add automatic agent scheduling, LangGraph, Agents SDK, Codex runtime bridge, generic subprocess launch, solver execution, QueueRunner launch, enqueue, direct ODB open, or automatic metrics extraction.

Codex/LLM summary is not final evidence. Final evidence must come from trace files, handoffs, gates, validators, diagnosis, metrics, artifact hashes, or explicitly documented limitations.

## ACOM Template Pack

Stage 5.0C places ACOM templates on this protocol. ACOMAgent is a support station that creates pipeline RUN/HANDOFF records plus `codex_handoff/` packages. It does not schedule agents, call Codex CLI, run solver, open ODB, or make final evidence claims.

Stage 5.0D adds ACOM result intake. ACOMAgent may classify `structured_result.json`, reject unsafe returns, and route accepted results to downstream AbqPilot revalidation through RUN/HANDOFF/GATE records. It does not approve evidence or invoke the downstream agent automatically.
