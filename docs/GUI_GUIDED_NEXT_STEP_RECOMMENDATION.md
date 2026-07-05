# GUI Guided Next-Step Recommendation

Stage 5.1E adds deterministic guided next-step recommendation to the GUI.

The recommender reads existing GUI workflow state, safe action catalog entries, trace viewer state, and artifact preview state. It produces advisory view models that explain:

- current workflow state
- latest status and gate decision
- recommended next safe action
- panel containing the action
- rationale
- prerequisites and missing prerequisites
- expected outputs
- final evidence effect
- disabled high-risk actions
- user instructions and safety boundaries

Recommendations are advisory only. They are not automatic execution. The GUI does not add a generic "execute recommendation" callback, does not auto-click actions, and does not auto-schedule agents.

The recommender preserves these boundaries:

- GUI does not call Codex CLI.
- External Codex operation remains human-operated and must return `codex_result/structured_result.json`.
- GUI does not run solver, open ODB, queue jobs, or schedule agents.
- GUI does not approve final evidence.
- GUI does not freeze final verdict.
- Non-solver acknowledgement remains non-final.
- Final evidence remains locked.

Recommended actions refer only to existing safe GUI panels and safe action catalog entries. High-risk downstream agents such as GuardAgent, CandidateBuilderAgent, DiagnosisAgent, ExecutionAgent, and MetricsAgent are not recommended for execution in this GUI stage.

Stage 5.1F validates these recommendation behaviors as part of the GUI beta end-to-end safe workflow smoke. The smoke is non-final and does not execute recommended actions.

Stage 5.2A high-risk gate UX previews may be referenced by recommendations as future-stage requirements only. They are not approval, not execution, and not final evidence readiness.
