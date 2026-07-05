# GUI Trace Viewer and Timeline Interaction

Stage 5.1C adds a read-only GUI trace viewer and timeline interaction layer.

The timeline contains eight non-solver ACOM workflow steps:

1. ACOM Handoff
2. ACOM Result Intake
3. Revalidation Scaffold
4. Non-Solver Revalidation
5. Supervisor Review
6. Non-Solver Ledger
7. Evidence Summary
8. Supervisor Ack

Selecting a timeline step resolves related evidence files and displays:

- RUN records
- HANDOFF records
- GATE records
- JSON artifacts
- Markdown reports
- current status
- latest gate decision
- claim boundary
- safety boundary
- missing files

Timeline selection is read-only. It does not execute agents, run solver, open ODB, call Codex CLI, queue jobs, approve gates, approve final evidence, or freeze verdict.

The viewer flags unsafe final-approval claims if frontmatter or JSON claims `final_evidence_approved=true`, `final_verdict_frozen=true`, `solver_approved=true`, `odb_metrics_approved=true`, `task_final_evidence_ledger_updated=true`, `codex_summary_is_final_evidence=true`, or unsafe automatic execution. The viewer only reports the issue; it does not modify files.

Final evidence remains locked.

Stage 5.1D builds on this viewer with read-only report and artifact previews. Markdown and JSON previews show frontmatter, headings, key sections, pretty JSON, safety fields, warning items, blocked items, and unsafe approval claims. Preview interactions do not edit artifacts, launch external editors, open external programs, run solver, open ODB, call Codex CLI, approve evidence, or freeze verdict.

Stage 5.1E adds guided next-step recommendation using the same workflow and trace state. Timeline state may inform a recommendation, but the recommendation remains advisory and does not execute agents, call Codex CLI, approve evidence, or freeze verdict.

Stage 5.1F includes trace viewer and timeline interaction in the GUI beta smoke. The smoke confirms timeline navigation remains read-only.
