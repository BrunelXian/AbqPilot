# AbqPilot Project Policy

Current accepted status:

```text
PASS_ABQPILOT_V2_STAGE3_8A_PATCH_QUEUE_PRODUCTION_REAL_ENQUEUE_SMOKE_READY
```

AbqPilot is a controlled Abaqus workflow system. Its runtime authority belongs to AbqPilot-owned deterministic tools, validators, guards, status checks, metric extraction, and evidence packaging.

Use Codex to build AbqPilot. Do not make Codex the agent.

Codex may be used manually as an optional development assistant for engineering work on this repository. Codex is not a runtime dependency, not the core simulation agent, and not authorized to directly submit Abaqus jobs, mutate simulation-critical assets outside tool contracts, open ODB files, or freeze evidence.

Future LLM use must be schema-bound and subordinate to deterministic AbqPilot tools. LLMs may help interpret intent, select safe tools, propose repair plans, and draft reports, but they must not directly mutate simulation-critical files, invent metrics, bypass guards, or make final physical claims.

Stage 3.5A adds an optional DeepSeek/ChatAnywhere-compatible provider contract and a deterministic mock reasoner. Stage 3.5B allows a compact sanitized task summary to be sent to the configured provider only after explicit confirmation. Stage 3.6 allows a sanitized deterministic repair context to be sent only after explicit confirmation so the provider can propose a schema-bound candidate patch proposal. Stage 3.7 may convert a validated proposal into a deterministic PatchBuilder candidate INP preview, but only in a new preview directory and only after StaticValidator, DiffGuard, and PhysicsGuard run. Stage 3.8 may pass a validated candidate INP preview into the existing guarded abqjobpilot queue workflow through preflight, dry-run enqueue, candidate-specific approval token, optional controlled real queue-only enqueue, and read-only status polling. Stage 3.8A confirmed one production patch candidate queue-only enqueue: queue-only true, solver/runner/gui false, only `runtime/queue.json` changed, and status polling remained read-only. Codex CLI remains the development tool and is not the AbqPilot runtime LLM. Real provider calls require explicit CLI or GUI confirmation, API keys are masked, task summaries and patch contexts are sanitized, and returned reasoning/proposals must pass strict JSON safety validators before they are displayed or used as advisory context. LLM proposals cannot mutate INP files, write CAE files, enqueue jobs, submit solvers, open ODB files, or bypass validators.

abqjobpilot integration is preview-only through Stage 2.5, queue-only in Stage 2.6, and read-only status monitoring in Stage 2.7. AbqPilot may call the public `abqjobpilot.api` preflight API from a configured local project root to create request and command-preview artifacts. Stage 2.4 calls abqjobpilot public enqueue API only with `dry_run=True`. Stage 2.5 creates and validates human approval artifacts. Stage 2.6 may call `enqueue(..., dry_run=False)` only after all approval, hash, config, and queue-only proof gates pass. Stage 2.7 may call only `status()` and `locate_outputs()` to read queue/status/output metadata. Stage 2.8 may validate existing output evidence but does not open ODB files. Stage 2.9 may generate deterministic evaluation and repair-plan artifacts but does not mutate INP files. Stage 3.8 patch-to-queue reuses the same guarded abqjobpilot adapter and requires a candidate-specific approval token before real queue-only enqueue. Stage 3.4 GUI Beta reads task workspace artifacts and routes safe actions through `GuiActionController`. Stage 3.x GUI/reporting layers must not submit Abaqus, launch QueueRunner, mutate runtime live status or reports, run `run_gui.py`, open ODB files outside the gated metrics extractor, auto-repair INP, or import abqjobpilot GUI modules. Stage 2.3A uses abqjobpilot as an importable public API package for preflight only. The abqjobpilot GUI does not need to be opened.

High-risk transitions require human approval, including solver submission, material or geometry changes, mesh changes, boundary-condition changes, guard relaxation, evidence freeze, and destructive run-directory operations.
