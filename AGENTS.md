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
