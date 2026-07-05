# GUI Report Viewer and Artifact Preview

Stage 5.1D adds read-only report viewer and artifact preview polish.

The preview layer can display Markdown reports, RUN / HANDOFF / GATE records, YAML frontmatter, JSON artifacts, non-solver ledgers, non-solver evidence summaries, and supervisor acknowledgement reports.

Preview models are read-only. They may parse text, classify artifact type, extract Markdown headings, extract key sections, pretty-print JSON, and surface safety fields. They must not edit, delete, rename, mutate, execute, or launch external editors or external programs.

The viewer displays:

- path and filename
- artifact type
- parse status
- frontmatter or JSON top-level keys
- status and decision fields
- safety fields
- Claim Boundary sections
- Safety Boundary or Guardrails sections
- warnings, blocked items, and unsafe approval claims

Unsafe approval claims are flagged, not fixed. The previewer reports claims such as `final_evidence_approved=true`, `final_verdict_frozen=true`, `solver_approved=true`, `odb_metrics_approved=true`, `task_final_evidence_ledger_updated=true`, `codex_summary_is_final_evidence=true`, `solver_run=true`, `queue_runner_launched=true`, `odb_opened=true`, `codex_cli_called=true`, or `shell_true_used=true`.

Stage 5.1D does not run solver, open ODB, launch QueueRunner, queue jobs, call Codex CLI, execute agents, approve gates, approve final evidence, freeze final verdict, update `TASK_FINAL_EVIDENCE_LEDGER.md`, or open external editors.

Final evidence remains locked. Solver / ODB / metrics remain disabled. Codex output is structured input, not final evidence.

Stage 5.1E uses these read-only preview states as part of guided next-step recommendation. Recommendations are advisory and do not execute previewed artifacts or add a generic execute button.

Stage 5.1F includes artifact/report preview checks in the GUI beta smoke. The smoke verifies read-only preview behavior and unsafe-claim detection without mutating artifacts.
