# Pipeline Communication Protocol

AbqPilot pipeline communication is file based and explicit. Agent-to-agent communication is allowed only through `HANDOFF_XXX.md` files. Each station records work in a `RUN_XXX.md` file. High-risk transitions require `GATE_XXX.md`.

## Document Types

- `run_report`: station execution trace plus supervisor step report.
- `handoff`: station-to-station input contract.
- `gate_decision`: high-risk transition decision.
- `task_plan`: task objective, scope, inputs, and risk.
- `trace_index`: index of flat trace, handoff, gate, and artifact entries.
- `final_evidence_ledger`: artifact-backed final evidence ledger.

## YAML Frontmatter

All key Markdown files start with YAML frontmatter. The minimal parser in `abqpilot.pipeline_protocol.frontmatter` validates required fields without adding a PyYAML dependency.

## Handoff Discipline

Each handoff states context, receiver inputs, required task, allowed actions, forbidden actions, required outputs, acceptance criteria, and gate requirement. A station may reject a handoff when required artifacts or frontmatter are missing.

## Evidence Boundary

Codex/LLM summary is not final evidence. ACOM support outputs must return through validators, MCPGuard, diagnosis, metrics, gates, or final ledger review before evidence claims are made.

## ACOM Template Handoffs

Stage 5.0C ACOM templates generate protocol-native handoffs. The ACOM run record is `trace/RUN_XXX_ACOM_<TEMPLATE_ID>.md`; the handoff record is `handoffs/HANDOFF_XXX_ACOM_TO_CODEX_OPERATOR.md`; and the bounded package is stored in `codex_handoff/`. The handoff must state that Codex auto execution is false, Codex summary is not final evidence, and AbqPilot revalidation is required.

Stage 5.0D ACOM result intake generates protocol-native return records: `trace/RUN_XXX_ACOM_RESULT_INTAKE.md`, `gates/GATE_XXX_ACOM_RESULT_REVALIDATION.md`, and `handoffs/HANDOFF_XXX_ACOM_RESULT_TO_<DOWNSTREAM_AGENT>.md`. Accepted intake uses `decision: PENDING_REVALIDATION`; rejected or blocked intake must not create an approved evidence gate.

Stage 5.0E downstream ACOM revalidation scaffold creates protocol-native downstream records: `RUN_XXX_<DOWNSTREAM_AGENT>_REVALIDATION.md`, `GATE_XXX_<DOWNSTREAM_AGENT>_REVALIDATION.md`, and `HANDOFF_XXX_<DOWNSTREAM_AGENT>_REVALIDATION_TO_<NEXT_AGENT_OR_SUPERVISOR>.md`. These are scaffold records only. They do not automatically run downstream agents and do not approve evidence.

Stage 5.0F non-solver revalidation may add `RUN_XXX_<AGENT>_REVALIDATION_RESULT.md`, `GATE_XXX_<AGENT>_REVALIDATION_RESULT.md`, and `HANDOFF_XXX_<AGENT>_REVALIDATION_RESULT_TO_PIPELINE_SUPERVISOR.md` for supported low-risk agents. The gate decision is `PENDING_SUPERVISOR_REVIEW` or `BLOCKED`, never `APPROVED`.

Stage 5.0G PipelineSupervisor review may add `RUN_XXX_PIPELINE_SUPERVISOR_NON_SOLVER_REVIEW.md`, `GATE_XXX_SUPERVISOR_NON_SOLVER_REVIEW.md`, and an accepted handoff to EvidenceReportAgent. Accepted review is ledger-only and non-final.
