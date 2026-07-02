# AbqPilot Codex Integration Strategy

## Final Decision

AbqPilot shall not embed the Codex desktop application as a runtime dependency.
Codex CLI may be used as an optional development assistant.
Production runtime must use OpenAI API / Agents SDK plus AbqPilot-owned deterministic tools.

Use Codex to build AbqPilot. Do not make Codex the agent.

## Phase Policy

Development phase: Codex CLI may be used manually as an external engineering assistant.

Prototype phase: AbqPilot Supervisor may later call Codex CLI or Codex MCP only for software-development assistance tasks.

Production and paper-grade runtime phase: use OpenAI API / Agents SDK plus AbqPilot-owned deterministic Abaqus tools. Do not rely on Codex CLI as the core Abaqus execution engine.

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
