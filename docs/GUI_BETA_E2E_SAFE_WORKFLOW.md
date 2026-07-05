# GUI Beta E2E Safe Workflow

Stage 5.1F performs a GUI end-to-end safe workflow smoke for the non-solver ACOM governance cockpit.

Stage 5.2A begins the high-risk UX design phase after this beta smoke. It specifies locked, preview-only high-risk gate requirements and does not add execution, approval, final evidence, or verdict-freeze capability.

Stage 5.2B adds controlled-solver-specific gate preview and inactive approval token design. It remains preview-only and does not create solver requests, active approval gates, or execution capability.

Stage 5.2C adds an inactive controlled solver human gate draft. It remains a GUI/specification artifact only and does not create active task gates, solver requests, or executable handoffs.

This is GUI beta readiness for non-solver ACOM governance. It is not final evidence readiness, not solver readiness, not ODB readiness, not metrics readiness, and not Codex automation readiness.

The smoke validates that the GUI can safely compose:

- workflow state
- safe action catalog
- visual layout sections
- workflow timeline
- trace viewer
- timeline interaction
- artifact preview
- report viewer card
- guided next-step recommendation
- disabled high-risk actions
- final evidence locked boundary
- external/manual Codex boundary
- solver / ODB / metrics disabled boundary
- unsafe final-approval claim detection

The generated `gui_beta/GUI_BETA_E2E_SMOKE_RESULT.json`, `gui_beta/GUI_BETA_E2E_SMOKE_REPORT.md`, and `gui_beta/GUI_BETA_CHECKLIST.md` are non-final project records.

The smoke does not execute recommended actions, does not add a generic execute recommendation callback, does not run solver, does not open ODB, does not call Codex CLI, does not queue jobs, does not auto-schedule agents, does not approve final evidence, does not freeze final verdict, and does not update `TASK_FINAL_EVIDENCE_LEDGER.md`.

Disabled high-risk actions remain visible and callback-free. Recommendations are advisory; no automatic execution. Unsafe final-approval claims are flagged, not fixed.
