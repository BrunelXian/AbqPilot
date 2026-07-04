# AbqPilot GUI Beta

Stage 3.4 upgrades the local `tkinter` GUI into a safe workflow cockpit. It is a local desktop UI over existing deterministic AbqPilot task workspace artifacts and safe CLI-equivalent functions.

## Layout

```text
-----------------------------------------------------------------------
| AbqPilot-v2 | Task: <task_id> | Overall: <status> | Refresh | Report |
-----------------------------------------------------------------------
| Left Sidebar              | Center Event Stream       | Right Panel |
| - Load task               | [timestamp] module event  | Current Module
| - Recent tasks            | [timestamp] action result | Status
| - Pipeline steps          | [timestamp] artifact      | Stage
| - Artifacts               |                           | Inputs
| - Workflow presets        |                           | Outputs
|                           |                           | Next Allowed Action
-----------------------------------------------------------------------
| Bottom status: Ready / Running / Waiting / Blocked / Failed          |
-----------------------------------------------------------------------
```

## Safe Actions

Visible safe actions:

- Load Task
- Refresh
- Run Prepare Pipeline
- Create Approval Token
- Poll JobPilot Status
- Continue From Job Output
- Generate Repair Plan
- Export Run Report
- Open Artifact Folder
- Run Mock Reasoner
- Preview LLM Input Summary
- Run Real LLM Reasoner
- Propose Patch with Mock LLM
- Preview Patch Context
- Propose Patch with Real LLM
- Preview Guarded Patch
- Prepare Controlled Solver Run
- Approve Controlled Solver Run
- Run Approved Solver
- Monitor Solver Run
- Diagnose Job / ODB Output
- Propose Solver Failure Repair
- Intake Solver Output
- Report Solver Run
- Generate Codex Handoff
- Validate Codex Handoff
- Intake Codex Result
- Report Codex Handoff

Each action goes through `GuiActionController`, catches exceptions, and returns a structured result dictionary. The controller calls existing AbqPilot functions rather than introducing new runtime paths.

Stage 5.0A GUI actions support ACOM handoff package generation, validation, structured result intake, and reporting. They do not run Codex CLI, run solver, queue jobs, open ODB files, or auto-execute returned work. Codex summaries are not final evidence; AbqPilot deterministic revalidation remains required.

## Disabled Actions

Dangerous workflow actions remain disabled in GUI Beta:

- arbitrary Abaqus solver execution
- external queue-worker launch
- LLM agent execution
- automatic INP repair
- patch application
- batch auto loops
- arbitrary command execution
- Codex auto execution

Disabled actions return `ACTION_BLOCKED_BY_SAFETY_BOUNDARY`.

## Right Panel

The right panel is the current worker panel. It displays:

- Current Module
- Module Status
- Stage
- Input Summary
- Output Summary
- Last Artifact
- Guard State
- Next Allowed Action
- Active Artifacts

Current-module selection prioritizes failed, running, waiting, or blocked steps before falling back to the latest completed step.

## Artifact Viewer

The artifact viewer supports:

- `.json` pretty print
- `.md`, `.txt`, `.log`, `.csv` plain text preview
- large-file truncation at 1 MB
- path-only display for binary or unknown files

It never executes, imports, or launches artifact files.

## Reasoning Panel

Stage 3.5B adds a read-only reasoning panel. It displays:

- Observation
- Diagnosis
- Recommended Next Action
- Risk Flags
- Human Review Required
- Confidence
- Safety Validator Status

`Run Mock Reasoner` never calls the network. `Preview LLM Input Summary` builds the compact sanitized JSON that would be sent and does not call a provider. `Run Real LLM Reasoner` requires an explicit confirmation dialog and sends only the sanitized task summary to the configured provider. It never sends full INP, ODB, CAE, full logs, raw `.env`, or secrets.

## Patch Proposal Panel

Stage 3.6 adds a patch proposal panel. It displays:

- Proposal Verdict
- Patch Type
- Rationale
- Expected Effect
- Guard Requirements
- Risk Flags
- Safety Validator
- Human Review Required

`Preview Patch Context` does not call a provider. `Propose Patch with Mock LLM` is deterministic and offline. `Propose Patch with Real LLM` requires explicit confirmation and sends only sanitized patch context. Stage 3.6 does not include an Apply Patch button; any placeholder remains disabled for a future guarded PatchBuilder stage.

Stage 3.7 adds `Preview Guarded Patch`. It reads a validated candidate proposal and calls deterministic PatchBuilder preview logic. A candidate INP can be written only in a new `patch_previews/preview_*` directory, and only for supported patch types. The original INP is not overwritten. StaticValidator, DiffGuard, and PhysicsGuard results are shown in the patch panel.

Stage 3.8 adds safe patch-to-queue actions:

- Queue Patch Preview: Preflight
- Queue Patch Preview: Dry-Run Enqueue
- Create Patch Queue Approval Token
- Queue Patch Preview: Real Queue-Only Enqueue
- Poll Patch Queue Status

These actions operate only on validated Stage 3.7 preview artifacts. The approval token is candidate-specific and is not interchangeable with the original task enqueue token. Real queue-only enqueue remains guarded by the existing abqjobpilot adapter and approval checks. The GUI does not provide solver execution, external queue-worker launch, ODB opening, LLM execution authority, or automatic closed-loop repair.

Stage 3.9 adds patched-job continuation actions:

- Poll Patched Job Status
- Intake Patched Job Output
- Extract Patched Job Metrics
- Report Patched Job

These actions read patch queue workflow artifacts and existing output evidence. Output intake accepts only an existing unlocked `.odb` path and records it without opening the file. Metrics extraction remains blocked until output is accepted and then uses only the existing gated metrics extractor. The GUI still does not start solver execution, launch QueueRunner, or open ODB files directly.

Stage 4.0 adds controlled solver automation actions:

- Prepare Controlled Solver Run
- Approve Controlled Solver Run
- Run Approved Solver
- Monitor Solver Run
- Diagnose Job / ODB Output
- Propose Solver Failure Repair
- Intake Solver Output
- Report Solver Run

These actions operate only on a validated sanity-base-derived candidate INP. The preparation step writes a fixed command preview for one Abaqus job and checks traceability, hashes, changed-line counts, StaticValidator, DiffGuard, PhysicsGuard, CPU limit, and run-directory safety. Solver launch requires the exact solver approval phrase and a token bound to the candidate, source, command preview, expected ODB, guard results, and CPU count. The GUI does not expose arbitrary command text, extra Abaqus flags, batch loops, QueueRunner launch, abqjobpilot GUI launch, or LLM execution authority.

Stage 4.1 adds `Diagnose Job / ODB Output`. It reads Abaqus text logs/status files and ODB/lock metadata, displays diagnosis status, failure category, ODB acceptability, completion evidence, failure evidence, important error lines, and the recommended next action. It does not launch solver execution and does not open ODB files.

Stage 4.2 adds `Propose Solver Failure Repair`. It consumes the Stage 4.1 diagnosis artifact and displays diagnosis status, failure category, recommended repair type, allowed and forbidden patch scopes, human-review requirement, and next allowed action. It does not apply repairs, mutate INP files, run solvers, enqueue jobs, open ODB files, or use LLM execution authority.

Stage 4.1B adds safe abqjobpilot record diagnosis actions. `List abqjobpilot Job Records` reads the runtime record files without mutation. `Diagnose from abqjobpilot Record` uses abqjobpilot's structured job paths as the execution record authority, then lets AbqPilot apply ODB validity and failure diagnosis. These actions do not launch QueueRunner, do not open the abqjobpilot GUI, do not submit Abaqus, and do not open ODB files directly.

Stage 4.3 adds `Preview DFLUX Deactivation Patch`. It creates a preview INP copy with explicit `*Dflux, OP=NEW` in `Step_cool_00`, displays validation status, unrelated changes, human-review requirement, and next allowed action. It does not apply patches in place, run solver, queue jobs, launch Abaqus/CAE, launch QueueRunner, or open ODB files.

Stage 4.4 adds DFLUX-guarded solver actions: `Prepare DFLUX-Guarded Solver Run`, `Approve DFLUX-Guarded Solver Run`, `Run Approved DFLUX-Guarded Solver`, `Monitor DFLUX-Guarded Solver`, `Intake DFLUX-Guarded Solver Output`, and `Report DFLUX-Guarded Solver Run`. Preparation enforces the Stage 4.3 DFLUX lifecycle guard before creating the solver run directory. The run action still requires a DFLUX-specific approval token and does not expose arbitrary Abaqus commands, QueueRunner launch, abqjobpilot GUI launch, uncontrolled ODB opening, auto retry, or LLM execution authority.

Stage 4.5 adds `Run Model Condition Preservation Guard`. It displays source JNL, source INP, candidate INP, solver INP, declared target change, guard status, condition findings, target patch isolation, solver eligibility, and recommended actions. It does not run solver, open ODB, auto-repair, or auto-retry.

## Workflow Presets

GUI Beta provides safe preset descriptions:

- Prepare Only
- Approval + Queue Only
- Status Poll Only
- Completed Output Intake
- Analysis / Repair Plan
- Report Export

Presets describe recommended next actions. They do not automatically execute an entire chain without user action.

## Safety Boundary

GUI Beta does not expose arbitrary Abaqus commands, does not start external queue workers, does not open the abqjobpilot GUI, does not add LangGraph/Codex runtime integration, and does not mutate INP files from repair plans or LLM patch proposals. Stage 4.0 controlled solver launch is limited to one validated sanity-base-derived candidate with a solver-specific approval token and a fixed command preview. Patch-to-queue supports preflight and dry-run preview by default; real queue-only enqueue requires a candidate approval token. Real LLM reasoning and patch proposal review are optional, explicitly confirmed, read-only, and advisory.
## Pipeline Protocol GUI Actions

GUI Beta may expose safe protocol actions:

- List Pipeline Agents
- Scaffold Pipeline Task
- Validate Pipeline Protocol
- Report Pipeline Protocol

These actions display agent lists, task directories, trace files, handoff files, gate files, validation status, and report paths. They must not provide Run Agent, Auto Schedule Pipeline, Run Codex, Run Solver, Open ODB, or Queue Job actions.

## ACOM Template GUI Actions

GUI Beta may expose safe ACOM template actions:

- List ACOM Templates
- Describe ACOM Template
- Generate Pipeline ACOM Handoff
- Validate ACOM Template Pack

These actions display template ID, risk level, MCPGuard requirement, producer/receiver agents, RUN/HANDOFF requirement, gate requirement, Codex auto-execution status, and AbqPilot revalidation requirement. They do not run Codex, auto-execute Codex, run solver, open ODB, queue jobs, or auto-schedule the pipeline.

## ACOM Result Intake GUI Actions

GUI Beta may expose safe Stage 5.0D actions:

- Intake ACOM Result
- Report ACOM Result Intake

These actions display task ID, handoff ID, template ID, result status, safety flags, artifact review, downstream agent, gate decision, AbqPilot revalidation requirement, and report path. They do not run Codex, auto-execute Codex, run solver, open ODB, queue jobs, or auto-schedule downstream agents.
