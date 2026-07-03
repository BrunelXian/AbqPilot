# AbqPilot Agent Governance

This repository is AbqPilot-v2 only. Do not migrate from or modify the previous V1 experimental project.

## Mission

AbqPilot is a closed-loop CAE-ODB automation system for controlled Abaqus simulation workflows.

## Non-negotiable safety rules

1. Do not modify material definitions unless explicitly requested and guarded.
2. Do not modify geometry, mesh, sets, steps, boundary conditions, or loads outside declared editable regions.
3. Do not claim a job completed unless ODB, lock-file, status-file, and final-frame/status checks pass.
4. Do not claim physics success unless metric extraction and guards pass.
5. Do not freeze evidence unless hashes, logs, metric JSON, and report files are generated.
6. Do not bypass StaticValidator, DiffGuard, PhysicsGuard, or ODB status checks.
7. Do not let Codex, LLMs, GUI, or CLI bypass deterministic AbqPilot tools.
8. Do not validate only the target edit. Also validate that non-target original model conditions are preserved across CAE export, INP patching, candidate generation, and solver-run copies.

## Hard Rule: SanityBase-Derived Simulation Candidates Only

AbqPilot must not create arbitrary new Abaqus models for production or evidence workflows.

The canonical simulation baseline is the user-provided sanity base model:

```text
D:\Projects\AbqPilot-v2\CAE_model\sanity_base\sanity_base_v01.cae
```

and the real Abaqus INP files exported from that sanity base through the gated CAE export path.

The agent's role is not to invent geometry, mesh, material definitions, boundary conditions, contact definitions, or step topology. The agent's role is to perform controlled, auditable modifications to the existing sanity base model or to an INP deterministically exported from it.

Allowed production candidate path:

```text
sanity_base_v01.cae
-> gated CAE writeInput export
-> real source INP
-> deterministic allowed patch
-> candidate INP
-> StaticValidator
-> DiffGuard
-> PhysicsGuard
-> solver / queue / ODB intake only through gated workflow
```

Acceptable fallback production candidate path:

```text
previously frozen real sanity-base exported INP
-> deterministic allowed patch
-> candidate INP
-> StaticValidator
-> DiffGuard
-> PhysicsGuard
```

Fixture INP files used by tests or workflow smoke checks must never be treated as solver-ready production evidence unless explicitly classified as real sanity-base-derived Abaqus exports.

In particular, tiny fixture files such as 1 KB INP snippets may be used to test PatchBuilder, DiffGuard, PhysicsGuard, queue workflow, or CLI behavior, but they must not be used as real Abaqus solver candidates or as evidence of physical simulation success.

For any production or demo claim involving Abaqus solver output, the candidate INP must be traceable to the user-provided sanity base model or to a frozen real INP exported from it.

The agent must record this traceability in evidence artifacts:

* source CAE path or frozen exported INP path
* source INP SHA256
* candidate INP SHA256
* exact allowed patch operation
* changed lines
* unrelated changes count
* StaticValidator result
* DiffGuard result
* PhysicsGuard result
* Model Condition Preservation Guard result when available

If the source candidate is not traceable to the sanity base model, the workflow must stop with a warning rather than continue to solver, queue, ODB intake, metrics extraction, or physical interpretation.

Production candidates must also preserve original model-condition intent. A valid patch is not only the intended target edit; it must also avoid losing or drifting non-target conditions such as load lifecycle, boundary lifecycle, interaction lifecycle, amplitudes, step procedures, output requests, set/surface/instance references, and other original CAE/JNL intent. Future solver eligibility should include StaticValidator, DiffGuard, PhysicsGuard, and the Model Condition Preservation Guard.

Recommended warning verdict:

```text
WARNING_ABQPILOT_SIMULATION_SOURCE_NOT_SANITY_BASE_DERIVED
```

## Codex policy

Use Codex to build AbqPilot. Do not make Codex the agent.

Codex is allowed as a development assistant.
Codex is not allowed as the core runtime agent.
Codex must not directly submit Abaqus jobs.
Codex must not directly mutate simulation-critical files outside AbqPilot tool contracts.
Codex must not freeze evidence or decide final physical claims.

## Runtime Boundary

MVP-01 and Stage 2 remain deterministic Python orchestration with structured schemas, controlled builders, static validation, diff guard, physics guard, gated CAE export, gated ODB metrics extraction, trace writing, and rollback placeholders.

LLM nodes are placeholders only and must not be invoked in the current accepted stage.

## Allowed development commands

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m pytest -q
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli status
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli --help
```

## Abaqus execution boundary

Abaqus job submission must be performed only through approved AbqPilot job tools.
Manual Abaqus commands must be emitted as handoff instructions unless the current phase explicitly allows automatic execution.
Abaqus CAE export and ODB metrics extraction must remain gated.
