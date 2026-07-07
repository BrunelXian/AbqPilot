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
9. Non-solver revalidation execution may only run for explicitly supported low-risk agents. High-risk model/solver/ODB agents must be blocked in Stage 5.0F.
10. A non-solver revalidation PASS only permits PipelineSupervisor review. It does not approve final evidence.
11. PipelineSupervisor non-solver review may only accept non-solver revalidation results into NON_SOLVER_EVIDENCE_LEDGER.
12. PipelineSupervisor non-solver review must not freeze final evidence and must not approve solver, ODB, metrics, model mutation, or high-risk agent results.
13. EvidenceReportAgent may summarize NON_SOLVER_EVIDENCE_LEDGER into a non-final report.
14. EvidenceReportAgent must not convert non-solver evidence into final evidence.
15. EvidenceReportAgent must not update TASK_FINAL_EVIDENCE_LEDGER.md in Stage 5.0H.
16. EvidenceReportAgent must not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.
17. PipelineSupervisor may acknowledge non-solver summary records into NON_SOLVER_SUMMARY_ACK_LEDGER.
18. PipelineSupervisor must not convert non-solver summaries into final evidence.
19. PipelineSupervisor must not update TASK_FINAL_EVIDENCE_LEDGER.md in Stage 5.0I.
20. PipelineSupervisor must not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.
21. GUI must not present non-solver acknowledgement as final evidence.
22. GUI disabled high-risk actions must not have executable backend callbacks.
23. GUI must preserve RUN/HANDOFF/GATE protocol visibility.
24. GUI must display final evidence locked unless a future explicit stage changes it.
25. GUI visual polish must not weaken safety boundaries.
26. GUI must not present disabled actions as executable.
27. GUI copy must distinguish non-final/non-solver records from final evidence.
28. GUI layout must preserve RUN/HANDOFF/GATE visibility.
29. GUI trace viewer must be read-only.
30. Timeline interaction must not execute backend actions.
31. Viewer must flag but not modify unsafe final approval claims.
32. Viewer must preserve final evidence locked state.

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

Default execution direction is ACOM, AbqPilot Codex Operator Mode. Codex may execute bounded handoff packages as an external human-operated operator, but AbqPilot remains the planner, validator, and evidence authority.

Codex summaries are not final evidence. AbqPilot must validate returned artifacts through deterministic schemas, guards, artifact hashes, tests, safety audits, secret audits, StaticValidator, DiffGuard, PhysicsGuard, MCPGuard when applicable, and Job/ODB diagnosis when applicable.

NARM, Native Agent Runtime Mode, is optional and must preserve the same safety and evidence contracts.

Accepted ACOM result must be routed into a downstream revalidation scaffold. No ACOM result may directly become evidence. No downstream revalidation may be auto-executed unless a future guarded stage explicitly implements it. Downstream revalidation must preserve RUN/HANDOFF/GATE protocol.

Use Codex to build AbqPilot. Do not make Codex the agent.

Codex is allowed as a development assistant.
Codex is not allowed as the core runtime agent.
Codex must not directly submit Abaqus jobs.
Codex must not directly mutate simulation-critical files outside AbqPilot tool contracts.
Codex must not freeze evidence or decide final physical claims.

ACOM templates must integrate with pipeline RUN/HANDOFF/GATE protocol. Do not generate isolated Codex prompts without pipeline trace. Do not auto-call Codex. Do not treat Codex natural-language summaries as evidence. Model-condition / INP-patch templates require MCPGuard or a documented not-applicable reason.

ACOM result intake must never directly approve evidence. It must classify Codex structured output, reject unsafe safety flags, reject task or handoff mismatch, and route accepted results to the appropriate downstream AbqPilot agent for deterministic revalidation. Codex summaries are not evidence. Accepted ACOM intake means pending revalidation only, not solver approval, ODB metrics approval, or final evidence freeze.

## Runtime Boundary

MVP-01 and Stage 2 remain deterministic Python orchestration with structured schemas, controlled builders, static validation, diff guard, physics guard, gated CAE export, gated ODB metrics extraction, trace writing, and rollback placeholders.

LLM nodes are placeholders only and must not be invoked in the current accepted stage.

## Pipeline-style agent protocol

Pipeline-style agent architecture is the default. Subagents are bounded pipeline stations, not a hierarchy of leads. The default station order is:

```text
PipelineSupervisor observes / gates / freezes
IntakeAgent -> AuditAgent -> CandidateBuilderAgent -> GuardAgent -> ExecutionAgent -> DiagnosisAgent -> MetricsAgent -> EvidenceReportAgent
```

Support agents are ACOMAgent, SoftwareQAAgent, and DocsStatusAgent.

Agent-to-agent handoff is allowed only through `HANDOFF_XXX.md`. Each step must produce `RUN_XXX.md`. High-risk transitions require `GATE_XXX.md`. No subagent may bypass validators, MCPGuard, diagnosis, approval tokens, or human gates. Do not validate only target edits; also validate original model-condition preservation across export, patching, candidate generation, and solver-run copies. Codex/LLM summary is not final evidence.

GUI artifact preview must be read-only. Preview modules must not open external editors, launch external programs, execute file contents, mutate artifacts, approve evidence, or freeze verdicts. Unsafe final approval claims must be flagged but not modified. `TASK_FINAL_EVIDENCE_LEDGER.md` must remain untouched in Stage 5.1D.

GUI next-step recommender must not add generic execution. Recommendations must preserve final evidence locked state, distinguish external Codex operation from GUI execution, and never imply final evidence approval. Recommendation text may point to existing safe panel actions, but it must not auto-click actions, auto-schedule agents, call Codex CLI, run solver, open ODB, queue jobs, approve final evidence, or freeze verdict.

GUI beta readiness is not final evidence readiness. GUI beta smoke reports are non-final project records and must not mutate `TASK_FINAL_EVIDENCE_LEDGER.md`. GUI beta smoke must not execute recommended actions and must preserve disabled high-risk action behavior.

High-risk gate UX previews must not be confused with approval. No "Approve" or "Execute" callbacks may be added in Stage 5.2A. High-risk prerequisites are advisory until a future explicit gate implementation, and the final evidence locked state must remain visible.

Controlled solver approval preview must not be treated as active approval. Human approval token validation in Stage 5.2B is preview-only. No Approve Solver or Run Solver callbacks may be added, and solver approval and solver execution must remain separated.

Inactive controlled solver gate draft must not be treated as active approval. Inactive draft validation must block active approval attempts. No Approve Solver, Create Active Gate, or Run Solver callbacks may be added, and solver approval and solver execution must remain separated.

Active controlled solver gate design must not be treated as real approval in Stage 5.2D. No active real task gates may be written in Stage 5.2D. No Approve Solver, Approve and Run, or Run Solver callbacks may be added. Solver approval and solver execution must remain separated.

Active gate writer fixture support must not be treated as real approval. Real task gates must not be written in Stage 5.2E. No Approve Solver, Approve and Run, or Run Solver callbacks may be added. Solver approval and solver execution remain separated.

Stage 5.2F smoke gate must not be treated as permission to execute solver. Active gate creation and solver execution remain separated. No arbitrary task gate writing is allowed in Stage 5.2F. No Run Solver or Approve and Run callbacks may be added.

Stage 5.2G handoff draft must not be treated as active execution permission. No active execution handoff may be written in Stage 5.2G. No solver request may be created in Stage 5.2G. No Run Solver or Execute Handoff callbacks may be added.

Stage 5.2H request draft must not be treated as an active solver request. No solver_request.json may be written in Stage 5.2H. No active execution request may be created in Stage 5.2H. No Run Solver or Execute Request callbacks may be added.

Stage 5.2I preflight pass must not be treated as solver execution permission. No solver_request.json may be written in Stage 5.2I. No active execution request may be created in Stage 5.2I. No Run Solver or Execute Request callbacks may be added. Preflight validates shape/policy only; it does not invoke solver.

Stage 5.2J dry-run request must not be treated as active solver request. No `solver_request.json`, `job_request.json`, or `abaqus_job.json` may be written in Stage 5.2J. No active execution request, queue submission, output execution directory, Run Solver, Submit Queue, Execute Request, or Approve and Run callback may be added. Dry-run materialization validates request shape only; it does not invoke solver.

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

Stage 5.3A-R workspace remediation establishes a hard patch-root policy after the failed Stage 5.3A attempt. Future Codex/apply_patch operations must confirm cwd, resolved project root, and git root before patching. The only valid project root is `D:\Projects\AbqPilot-v2`; `D:\Users\wuxia\Documents\AbqPilot` is forbidden except for explicitly approved cleanup. Relative patch paths must not be used unless cwd and git root are confirmed, every planned file target is listed as an absolute path, and a forbidden-root scan is run after patching. If any writer touches outside the project root, stop immediately and do not continue the implementation stage.

Stage 5.3A-v2 controlled solver demo smoke must use the Stage 5.3A-R workspace guard policy. It may create exactly one `solver_request.json` only under `runs/tasks/stage5_3a_v2_controlled_solver_demo_smoke/artifacts/solver_requests/` and may attempt only the fixed Abaqus command for the copied demo INP. No generic Run Solver, Approve and Run, Execute Request, QueueRunner, ODB open, metrics extraction, final evidence approval, final verdict freeze, or forbidden-root write may be added.
