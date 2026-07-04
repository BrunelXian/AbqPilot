# AbqPilot Codex Integration Strategy

## Final Decision

AbqPilot shall not embed the Codex desktop application as a runtime dependency.
Codex CLI may be used as an optional development assistant.
Current Stage 5.0B policy supersedes earlier native-agent planning: do not add Agents SDK, LangGraph, Codex runtime bridge, automatic Codex CLI execution, or automatic multi-agent scheduling in this stage.

Use Codex to build AbqPilot. Do not make Codex the agent.

## Phase Policy

Development phase: Codex CLI may be used manually as an external engineering assistant.

Prototype phase: AbqPilot may package support-agent handoffs for human-operated Codex assistance, but must not automatically call Codex CLI or Codex MCP in Stage 5.0B.

Production and paper-grade runtime phase: use AbqPilot-owned deterministic Abaqus tools and artifact-backed evidence. Any future OpenAI API or Agents SDK design would require a separate gated stage and is not part of the Stage 5.0B pipeline protocol.

## Runtime Responsibility Boundary

### LLM Reasoner

LLM Reasoner may:

- understand user intent
- read structured summaries
- select safe tools
- interpret validator output
- propose repair plans
- write human-readable reports

LLM Reasoner must not:

- directly mutate simulation-critical files
- invent ODB metrics
- claim a job succeeded without evidence
- bypass audits
- silently relax guards

### Deterministic Tools

Deterministic tools own:

- CAE-to-INP export
- INP patching
- StaticValidator
- DiffGuard
- PhysicsGuard
- Abaqus job lifecycle management
- ODB extraction
- metric evaluation
- evidence freeze

### Human Supervisor

Human supervisor owns:

- approving high-risk simulation changes
- launching expensive jobs
- accepting relaxed guard settings
- confirming paper-grade evidence

## Route B Policy

Codex CLI / Codex MCP may later be optional tools for software-development assistance only.

Do not implement it in this stage.
