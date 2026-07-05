# High-Risk Gate Checklist Preview

Prerequisites shown here are advisory/specification only. No real gate is created in Stage 5.2A.

## Controlled Solver Run

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `task_scaffold_exists`: Task scaffold exists.
- `candidate_inp_exists`: Candidate INP exists under an allowed task or run artifact directory.
- `static_validator_pass`: StaticValidator PASS record exists.
- `diff_guard_pass`: DiffGuard PASS record exists.
- `physics_guard_pass`: PhysicsGuard PASS record exists.
- `mcpguard_pass`: MCPGuard PASS record exists where model conditions or INP patches may be affected.
- `patch_preview_accepted`: Patch preview has been accepted as a preview artifact, not applied in place.
- `future_human_gate`: Explicit human solver gate approval record would be required in a future stage.
- `solver_command_configured`: Solver command path is configured in project status or config.
- `source_mutation_absent`: No source CAE/INP mutation occurred outside allowed copied artifacts.

## Queue Job

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `solver_readiness_design`: Controlled solver readiness design has been accepted.
- `job_manifest_exists`: Task or job manifest exists.
- `future_queue_gate`: Queue mutation gate is approved in a future explicit stage.
- `queue_json_risk_acknowledged`: queue.json write risk is acknowledged.
- `runtime_status_isolation`: Runtime status isolation is defined.

## Open ODB for Diagnosis

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `odb_under_allowed_artifact_dir`: ODB path exists under an allowed run artifact directory.
- `controlled_solver_completion_record`: Controlled solver completion record exists.
- `future_odb_acceptance_gate`: ODB acceptance gate is pending or required.
- `read_only_extractor_contract`: Read-only ODB extractor contract exists.
- `no_uncontrolled_interactive_open`: No uncontrolled interactive ODB opening is allowed.

## Extract ODB Metrics

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `future_odb_metrics_acceptance`: ODB is accepted for metrics in a future gate.
- `metrics_schema_exists`: Metrics schema exists.
- `extractor_contract_exists`: Extraction script contract exists.
- `metrics_output_target_defined`: Output JSON target is defined.
- `metrics_non_final_until_gated`: Metrics remain non-final until EvidenceReportAgent and PipelineSupervisor gates.

## Mutate Source CAE

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `source_mutation_justification`: Explicit source mutation justification exists.
- `backup_freeze_plan`: Backup and freeze plan exists.
- `diff_plan`: Diff plan exists.
- `irreversible_warning`: Irreversible mutation warning is acknowledged.
- `future_human_source_gate`: Human gate approval exists in a future explicit stage.

## Mutate Source INP

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `source_mutation_justification`: Explicit source mutation justification exists.
- `backup_freeze_plan`: Backup and freeze plan exists.
- `diff_plan`: Diff plan exists.
- `irreversible_warning`: Irreversible mutation warning is acknowledged.
- `future_human_source_gate`: Human gate approval exists in a future explicit stage.

## Accept Metrics for Evidence

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `future_odb_metrics_acceptance`: ODB is accepted for metrics in a future gate.
- `metrics_schema_exists`: Metrics schema exists.
- `extractor_contract_exists`: Extraction script contract exists.
- `metrics_output_target_defined`: Output JSON target is defined.
- `metrics_non_final_until_gated`: Metrics remain non-final until EvidenceReportAgent and PipelineSupervisor gates.
- `all_upstream_traces_complete`: All upstream RUN/HANDOFF/GATE traces are complete.
- `metrics_accepted`: Metrics are accepted through a future metrics gate.
- `final_evidence_ledger_draft`: Final evidence ledger draft is complete.
- `pipeline_supervisor_final_review`: PipelineSupervisor final review is complete.
- `future_final_freeze_stage`: Explicit human approval occurs in a future final freeze stage.

## Approve Final Evidence

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `all_upstream_traces_complete`: All upstream RUN/HANDOFF/GATE traces are complete.
- `metrics_accepted`: Metrics are accepted through a future metrics gate.
- `final_evidence_ledger_draft`: Final evidence ledger draft is complete.
- `pipeline_supervisor_final_review`: PipelineSupervisor final review is complete.
- `future_final_freeze_stage`: Explicit human approval occurs in a future final freeze stage.

## Freeze Final Verdict

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `all_upstream_traces_complete`: All upstream RUN/HANDOFF/GATE traces are complete.
- `metrics_accepted`: Metrics are accepted through a future metrics gate.
- `final_evidence_ledger_draft`: Final evidence ledger draft is complete.
- `pipeline_supervisor_final_review`: PipelineSupervisor final review is complete.
- `future_final_freeze_stage`: Explicit human approval occurs in a future final freeze stage.

## Delete or Overwrite Historical Artifact

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `historical_artifact_inventory`: Historical artifact inventory exists.
- `retention_policy`: Retention policy and replacement rationale are documented.
- `backup_plan`: Backup plan exists.
- `future_human_destructive_gate`: Human destructive-action gate exists in a future explicit stage.

## Run Codex from GUI

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `future_runtime_bridge_design`: Future explicit runtime bridge design exists.
- `security_boundary`: Security boundary is defined.
- `user_confirmation`: User confirmation is defined.
- `log_trace_policy`: Log and trace policy exists.
- `secret_leakage_controls`: No-secret-leak controls are defined.
- `abort_rollback_policy`: Abort and rollback policy exists.

## Auto Schedule Agent

- approval_status: `NOT_APPROVED`
- execution_status: `NOT_EXECUTABLE`
- preview_only: `True`

Prerequisites:
- `future_runtime_bridge_design`: Future explicit runtime bridge design exists.
- `security_boundary`: Security boundary is defined.
- `user_confirmation`: User confirmation is defined.
- `log_trace_policy`: Log and trace policy exists.
- `secret_leakage_controls`: No-secret-leak controls are defined.
- `abort_rollback_policy`: Abort and rollback policy exists.

