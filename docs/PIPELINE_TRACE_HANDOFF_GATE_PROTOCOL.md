# Pipeline Trace, Handoff, and Gate Protocol

Pipeline task workspaces use this scaffold:

```text
runs/tasks/<task_id>/
    TASK_PLAN.md
    TRACE_INDEX.md
    trace/
        RUN_001_INTAKE.md
        RUN_002_AUDIT.md
        RUN_003_CANDIDATE_BUILD.md
        RUN_004_GUARD_VALIDATION.md
        RUN_005_EXECUTION.md
        RUN_006_DIAGNOSIS.md
        RUN_007_METRICS.md
        RUN_008_EVIDENCE_REPORT.md
    handoffs/
        HANDOFF_001_INTAKE_TO_AUDIT.md
        HANDOFF_002_AUDIT_TO_CANDIDATE_BUILDER.md
        HANDOFF_003_CANDIDATE_BUILDER_TO_GUARD.md
        HANDOFF_004_GUARD_TO_EXECUTION.md
        HANDOFF_005_EXECUTION_TO_DIAGNOSIS.md
        HANDOFF_006_DIAGNOSIS_TO_METRICS.md
        HANDOFF_007_METRICS_TO_EVIDENCE_REPORT.md
    gates/
        GATE_001_ALLOW_CANDIDATE_BUILD.md
        GATE_002_ALLOW_EXECUTION.md
        GATE_003_ACCEPT_ODB_FOR_METRICS.md
        GATE_004_FREEZE_FINAL_EVIDENCE.md
    artifacts/
        run_001_intake/
        run_002_audit/
        run_003_candidate_build/
        run_004_guard_validation/
        run_005_execution/
        run_006_diagnosis/
        run_007_metrics/
        run_008_evidence_report/
    TASK_FINAL_EVIDENCE_LEDGER.md
```

`trace/` is flat and Markdown-only. Do not create per-run subdirectories under `trace/`. Evidence files belong under `artifacts/`.

## RUN_XXX.md

`RUN_XXX.md` is a human-readable execution trace and supervisor step report. It records purpose, inputs, actions, outputs, validation, forbidden-action confirmation, verdict, claim boundary, and next recommended step.

## HANDOFF_XXX.md

`HANDOFF_XXX.md` is an agent-to-agent input contract. It defines what the receiver may use and what it must produce.

## GATE_XXX.md

`GATE_XXX.md` is a high-risk transition decision. It records transition, risk, required conditions, evidence reviewed, decision, approver, reason, and residual risk.

## ACOM Template Records

Stage 5.0C ACOM template generation may add extra flat trace files such as `RUN_009_ACOM_MCPGUARD_REVIEW.md` and handoffs such as `HANDOFF_008_ACOM_TO_CODEX_OPERATOR.md`. High-risk or model-condition templates may add `GATE_005_PENDING_ACOM_RESULT_REVALIDATION.md` with `decision: PENDING_REVALIDATION`. This gate does not approve execution.

Stage 5.0D ACOM result intake may add `RUN_010_ACOM_RESULT_INTAKE.md`, `GATE_006_ACOM_RESULT_REVALIDATION.md`, and `HANDOFF_009_ACOM_RESULT_TO_<DOWNSTREAM_AGENT>.md`. These files keep the trace flat and Markdown-only. A safe result gate remains `PENDING_REVALIDATION`; unsafe or malformed results are `BLOCKED`.

Stage 5.0E may add downstream revalidation scaffold records such as `RUN_013_GUARD_AGENT_REVALIDATION.md`, `GATE_009_GUARD_AGENT_REVALIDATION.md`, and `HANDOFF_012_GUARD_AGENT_REVALIDATION_TO_PIPELINE_SUPERVISOR.md`. These keep `automatic_execution_performed: false` and do not approve evidence.

Stage 5.0F may add non-solver revalidation result records such as `RUN_016_DOCS_STATUS_AGENT_REVALIDATION_RESULT.md`, `GATE_012_DOCS_STATUS_AGENT_REVALIDATION_RESULT.md`, and `HANDOFF_015_DOCS_STATUS_AGENT_REVALIDATION_RESULT_TO_PIPELINE_SUPERVISOR.md`. These records are produced only by explicit CLI/GUI invocation for supported low-risk agents and keep `final_evidence_approved: false`.

Stage 5.0G may add supervisor review records such as `RUN_018_PIPELINE_SUPERVISOR_NON_SOLVER_REVIEW.md`, `GATE_014_SUPERVISOR_NON_SOLVER_REVIEW.md`, and `HANDOFF_017_SUPERVISOR_NON_SOLVER_REVIEW_TO_EVIDENCE_REPORT_AGENT.md`. These records may update `NON_SOLVER_EVIDENCE_LEDGER.md/json`, not `TASK_FINAL_EVIDENCE_LEDGER.md`.

Stage 5.0H may add EvidenceReportAgent non-solver summary records such as `RUN_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md`, `GATE_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md`, and `HANDOFF_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY_TO_PIPELINE_SUPERVISOR.md`. These records summarize the non-solver ledger only and must not update `TASK_FINAL_EVIDENCE_LEDGER.md`.

Stage 5.0I may add PipelineSupervisor acknowledgement records such as `RUN_XXX_PIPELINE_SUPERVISOR_NON_SOLVER_SUMMARY_ACK.md`, `GATE_XXX_SUPERVISOR_NON_SOLVER_SUMMARY_ACK.md`, and `HANDOFF_XXX_SUPERVISOR_NON_SOLVER_SUMMARY_ACK_TO_DOCS_STATUS_AGENT.md`. These records acknowledge a non-final non-solver summary only and must not update `TASK_FINAL_EVIDENCE_LEDGER.md`.
## Stage 5.1A GUI Trace Visibility

Stage 5.1A exposes the flat RUN/HANDOFF/GATE protocol in the GUI through read-only workflow-state inspection. The GUI shows trace, handoff, and gate counts plus latest status/decision without scheduling agents or approving transitions.

The GUI remains non-final and non-solver only: no Codex CLI call, no solver run, no ODB open, no QueueRunner launch, no automatic agent scheduling, no final evidence approval, and no final verdict freeze.

## Stage 5.1C Timeline Selection

The GUI trace viewer maps each ACOM/non-solver timeline step to related RUN/HANDOFF/GATE records and artifacts. Timeline selection is read-only and must not approve gates, execute agents, run solver, open ODB, call Codex CLI, queue jobs, or freeze evidence.

## Stage 5.1D Artifact Preview

The GUI report viewer can preview RUN/HANDOFF/GATE Markdown, JSON artifacts, ledgers, and summaries as read-only records. It may extract frontmatter, Markdown sections, pretty JSON, status/decision fields, and safety fields. It must not mutate records, open external editors, execute file contents, approve final evidence, or update `TASK_FINAL_EVIDENCE_LEDGER.md`. Unsafe approval claims are flagged, not fixed.

Stage 5.2A high-risk gate UX specifications are not real `GATE_XXX.md` approval records. They live under `gui_high_risk_gate_ux/`, are marked preview-only/specification-only/not-approved/not-executable, and must not be interpreted as task transition approval. Real high-risk gate decisions require a future explicit stage.

Stage 5.2B controlled solver gate preview records are also not real `GATE_XXX.md` approval records. Approval token validation in this stage is preview-only. Future real approval and future controlled solver execution must be represented by separate later stages.

Stage 5.2C inactive controlled solver gate draft records are not real `GATE_XXX.md` approval records either. Expected future active gate and execution handoff shapes may be written under the preview/spec directory, but they must not appear as active task transition records.

Stage 5.2D active controlled solver gate design records are still not real task `GATE_XXX.md` approval records. The schema can describe a future `APPROVED_BY_HUMAN` gate, but Stage 5.2D must not write that schema into real task `gates/`, must not write an active execution handoff into real task `handoffs/`, and must not create a solver request.
