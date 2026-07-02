# AbqPilot

**Turning Abaqus simulation iteration into a guarded, auditable closed-loop workflow.**

AbqPilot is a closed-loop CAE-ODB agent framework for Abaqus simulation automation. It is not a chatbot that freely edits Abaqus models. It is an Abaqus simulation task compiler with guarded CAE/INP mutation, deterministic validation, Abaqus job lifecycle control, gated ODB metric extraction, repair planning, rollback-oriented workflow state, and auditable evidence traces.

Engineering simulation is rarely a single generation step. Real Abaqus work moves through modeling, submission, failure inspection, ODB reading, metric judgment, repair, and another controlled run. That loop is expensive, stateful, and failure-prone. Silent physics changes are dangerous, and direct LLM-to-INP mutation is not an engineering control system.

AbqPilot exists to put an executable boundary between generative assistance and deterministic simulation governance:

**The LLM is not the authority; the guarded toolchain is.**

## Why AbqPilot Exists

A practical Abaqus iteration loop looks more like this:

```text
user goal
  -> sanity base model
  -> controlled CAE/INP mutation
  -> static validation
  -> diff guard
  -> physics guard
  -> Abaqus job lifecycle layer
  -> ODB extraction
  -> metric evaluation
  -> repair plan
  -> next iteration or fail-stop
```

AbqPilot is designed to engineer this observation-judgment-modeling-solving-reading-repair loop, not to generate a one-shot model from a prompt.

The core idea is simple: preserve useful INP/CAE generation and repair assistance while preventing uncontrolled material, geometry, mesh, load, boundary-condition, or physics changes. ODB feedback is compressed into structured metrics before it is used for repair reasoning. Every mutation, job handoff, output intake, and evidence freeze must be traceable.

## What AbqPilot Is

- An Abaqus closed-loop simulation workflow system.
- A controlled CAE/INP mutation framework built around declared editable regions.
- A deterministic validator and guard layer for static checks, diffs, and physics constraints.
- An ODB-feedback-driven evaluation and repair-planning workflow.
- An auditable task workspace, run-report, and evidence trace system.
- A human-supervised engineering automation cockpit for high-risk transitions.
- A place where schema-bound LLM reasoning can propose, but deterministic tools must validate.

## What AbqPilot Is Not

- Not a free-form Abaqus chatbot.
- Not a universal CAE model generator.
- Not an uncontrolled LLM-to-INP pipeline.
- Not a replacement for engineering judgment.
- Not a system that can bypass validation, physics guards, approval tokens, or evidence checks.
- Not a claim that arbitrary fracture, contact, UMAT, or general CAE model completion is already solved.

## Current MVP Scope

**MVP-01: AM thermal-control loop**

The current project focuses on a guarded additive-manufacturing thermal-control workflow. The repository defines and tests the contracts needed to:

- start from a sanity base Abaqus model or INP;
- modify only approved heat-flux-related parameters;
- run StaticValidator, DiffGuard, and PhysicsGuard checks;
- prepare or queue Abaqus work through controlled job tools and approval gates;
- intake completed solver outputs through explicit gates;
- extract NT11-oriented metrics through the gated ODB metrics path;
- evaluate a target-temperature objective;
- generate deterministic repair-plan artifacts;
- stop with an auditable `PASS`, `REPAIR`, or `FAIL_STOP` style decision.

Current boundaries are intentional:

- Abaqus solver execution is not automatic.
- Queue worker launch remains outside AbqPilot GUI authority.
- ODB access is limited to the gated metrics extractor.
- Repair plans are reports and do not directly mutate production INP files.
- LLM reasoning is optional, confirmation-gated, schema-bound, and advisory.
- LLM patch proposals cannot apply patches, enqueue jobs, open ODB files, or bypass guards.
- Patch preview currently targets heat-flux magnitude adjustment under validator-gated contracts.

## Architecture

```text
User Goal
   |
   v
Goal Compiler
   |
   v
Controlled Builder
   |
   v
StaticValidator / DiffGuard / PhysicsGuard
   |
   v
Abaqus Job Layer
   |
   v
ODB Extractor
   |
   v
Metric Evaluator
   |
   v
Repair Planner
   |
   v
PASS / REPAIR / FAIL_STOP
```

LLM nodes reason and propose. Deterministic tools validate, execute, extract, compare, and freeze evidence. Human supervisors approve high-risk transitions such as real queue enqueue, solver handoff, guard relaxation, material changes, geometry or mesh changes, and evidence freeze.

## Safety Principles

- No uncontrolled material modification.
- No geometry, mesh, set, step, load, or boundary-condition mutation outside explicit contracts.
- No PASS without ODB/status evidence and metric evaluation.
- No evidence freeze without hashes, logs, metrics, and reports.
- No Abaqus job execution outside approved job tools and approval gates.
- No ODB/CAE/JNL or large run artifacts in Git.
- No API keys, credentials, private certificates, or local `.env` files in Git.
- No LLM output can become an executable mutation without schema checks and deterministic guards.

## Repository Layout

```text
abqpilot/                 Core package
  analysis/               Metric evaluation and repair-plan logic
  builders/               Controlled INP/CAE construction helpers
  cae/                    CAE export and INP-related gates
  core/                   Pipeline runner, approval, and workflow steps
  execution/              Job lifecycle abstractions
  gui/                    Tkinter GUI beta cockpit
  integrations/           abqjobpilot adapter boundary
  llm/                    Optional schema-bound provider and safety contracts
  odb/                    Gated ODB metric extraction path
  patching/               Guarded patch proposal and queue workflows
  reporting/              Run reports, status, and evidence packaging
  tools/                  Validators, guards, and utility tools
configs/                  Example task configuration
docs/                     Architecture, CLI, GUI, LLM, and integration notes
tests/                    Contract and workflow tests
AGENTS.md                 Agent governance and non-negotiable safety rules
ABQPILOT.md               Project policy and accepted runtime boundaries
PROJECT_STATUS_CURRENT.*  Current capability and limitation snapshot
README.md                 Project overview
```

## Development Status

AbqPilot is in early-stage MVP development. The repository focuses on the guarded execution architecture, tool contracts, tests, configuration schemas, task workspace model, GUI beta cockpit, optional schema-bound LLM advisory layer, and initial closed-loop workflow components.

The current project status file records Stage 3.8A as a queue-only patch workflow smoke milestone: a validated patch candidate can pass through preflight, dry-run enqueue, candidate-specific approval, controlled queue-only enqueue, and read-only status polling. This is not the same as automatic solver execution or unrestricted repair.

For the exact current capability matrix and limitations, see:

- `PROJECT_STATUS_CURRENT.md`
- `ABQPILOT.md`
- `docs/ARCHITECTURE_V2.md`
- `docs/MVP01_THERMAL_CONTROL.md`
- `docs/LLM_PROVIDER_CONTRACT.md`

## Quick Checks

Use the project Python environment for local development checks. The commands below do not run Abaqus:

```powershell
python -m pytest -q
python -m abqpilot.cli status
python -m abqpilot.cli --help
```

Example dry workflow commands are documented in:

- `docs/CLI_USAGE.md`
- `docs/TASK_WORKSPACE.md`
- `docs/GUI_BETA.md`

## Roadmap

- **Stage 1:** AM thermal-control closed loop with guarded heat-flux mutation and NT11 metric evaluation.
- **Stage 2:** Broader thermo-mechanical metrics such as `U`, `U2`, `PEEQ`, `S`, and `NT11` under explicit extraction contracts.
- **Stage 3:** Abaqus model completion support under plugin-style contracts, not free-form generation.
- **Stage 4:** Domain plugin system for AM, fracture, contact, UMAT validation, and other specialized workflows.

The long-term direction is not a magical Abaqus agent. It is a controlled simulation operating layer where every proposed change has a contract, every run has evidence, and every repair decision can be audited.
