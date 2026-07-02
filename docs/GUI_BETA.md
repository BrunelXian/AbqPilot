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

Each action goes through `GuiActionController`, catches exceptions, and returns a structured result dictionary. The controller calls existing AbqPilot functions rather than introducing new runtime paths.

## Disabled Actions

Dangerous workflow actions remain disabled in GUI Beta:

- Abaqus solver execution
- external queue-worker launch
- LLM agent execution
- automatic INP repair
- patch application

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

GUI Beta does not submit Abaqus jobs, does not start external queue workers, does not open the abqjobpilot GUI, does not add LangGraph/Codex runtime integration, and does not mutate INP files from repair plans or LLM patch proposals. Patch-to-queue supports preflight and dry-run preview by default; real queue-only enqueue requires a candidate approval token. Real LLM reasoning and patch proposal review are optional, explicitly confirmed, read-only, and advisory.
