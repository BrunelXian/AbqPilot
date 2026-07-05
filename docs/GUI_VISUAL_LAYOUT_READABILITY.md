# GUI Visual Layout and Readability

Stage 5.1B polishes the Stage 5.1A GUI information architecture into a clearer safe workflow cockpit.

This stage adds presentation helpers for:

- top project header cards
- task workspace cards
- workflow timeline
- next safe action card
- disabled high-risk action card
- RUN / HANDOFF / GATE trace summary card
- grouped safe action panels
- deterministic badge labels

The workflow timeline displays:

1. ACOM Handoff
2. ACOM Result Intake
3. Revalidation Scaffold
4. Non-Solver Revalidation
5. Supervisor Review
6. Non-Solver Ledger
7. Evidence Summary
8. Supervisor Ack

Stage 5.1B does not add new execution capability. It does not run solver, open ODB, launch QueueRunner, queue jobs, call Codex CLI, auto-schedule agents, approve final evidence, approve solver/ODB/metrics, or freeze final verdict.

Stage 5.1D keeps the same boundary for report and artifact preview polish. Preview cards are read-only and do not open external editors, execute file contents, mutate artifacts, approve final evidence, or update `TASK_FINAL_EVIDENCE_LEDGER.md`.

Stage 5.1E adds a guided next-step recommendation card. The card explains which existing safe panel action to use, but it does not add automatic execution, a generic execute button, final evidence approval, or final verdict freeze.

Stage 5.1F freezes GUI beta readiness for the non-solver cockpit after an end-to-end safe workflow smoke. This is not a final evidence freeze.

Disabled high-risk actions remain visible but callback-free. Non-solver acknowledgement remains non-final, and `TASK_FINAL_EVIDENCE_LEDGER.md` remains locked.

Stage 5.1C builds on this layout with a read-only trace viewer. Timeline selection updates evidence detail cards only; it does not execute backend actions.
