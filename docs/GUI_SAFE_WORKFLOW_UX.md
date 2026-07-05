# GUI Safe Workflow UX

Stage 5.1A introduces a safe action catalog for GUI actions.

Allowed action categories:

- `SAFE_READ_ONLY`
- `SAFE_SCAFFOLD`
- `SAFE_NON_SOLVER_REVALIDATION`
- `SAFE_SUPERVISOR_NON_FINAL`

Disabled action categories:

- `DISABLED_HIGH_RISK`
- `DISABLED_FINAL_EVIDENCE`

Disabled high-risk actions are visible but have no executable backend callback:

- Run Solver
- Open ODB
- Queue Job
- Run Codex
- Auto Schedule Agent
- Approve Final Evidence
- Freeze Final Verdict
- Approve Solver / ODB / Metrics

For all Stage 5.1A GUI actions, final evidence effect is limited to `NONE` or `NON_FINAL_NON_SOLVER_RECORD_ONLY`.

It must never be:

- `FINAL_EVIDENCE_APPROVAL`
- `FINAL_VERDICT_FREEZE`

The GUI does not call Codex CLI, does not run solver, does not open ODB, does not launch QueueRunner, does not auto-schedule agents, and does not approve final evidence.

Stage 5.1D report and artifact previews are read-only. They display Markdown/JSON contents and flag unsafe final-approval claims, but they do not edit artifacts, launch external editors, run shell commands, fix files, approve evidence, or freeze verdicts.

Stage 5.1E recommendations are advisory. The GUI does not add a generic execute recommendation button, does not auto-click safe actions, does not call Codex CLI, and does not auto-schedule agents. Recommendation text must distinguish non-final/non-solver records from final evidence.

Stage 5.1F performs a GUI beta smoke across workflow state, trace navigation, artifact preview, recommendations, and disabled high-risk actions. The smoke reports GUI beta readiness only; it does not approve final evidence or freeze verdict.

Stage 5.2A adds high-risk gate UX specification. These previews describe prerequisites and warning copy for solver, ODB, queue, Codex, source mutation, metrics, final evidence, and final verdict gates, but they remain `PREVIEW_ONLY`, `NOT_APPROVED`, and `NOT_EXECUTABLE`.

## Stage 5.1B Readability Rules

Stage 5.1B keeps disabled high-risk actions callback-free while making them easier to see. It adds deterministic status cards and badges, but these are display-only. They must distinguish non-final/non-solver records from final evidence.

No visual label may imply final evidence approval, final verdict freeze, solver approval, ODB acceptance, or metrics approval.

Stage 5.1C timeline interaction is also read-only. Selecting a timeline step must not execute solver, ODB, Codex, queue, scheduling, agent execution, final evidence approval, or final verdict freeze.
