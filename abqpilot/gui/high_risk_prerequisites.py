from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HighRiskPrerequisite:
    prerequisite_id: str
    description: str
    stage_5_2a_status: str = "SPECIFICATION_ONLY"
    required_in_future_gate: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


CONTROLLED_SOLVER_RUN_PREREQUISITES = (
    HighRiskPrerequisite("task_scaffold_exists", "Task scaffold exists."),
    HighRiskPrerequisite("candidate_inp_exists", "Candidate INP exists under an allowed task or run artifact directory."),
    HighRiskPrerequisite("static_validator_pass", "StaticValidator PASS record exists."),
    HighRiskPrerequisite("diff_guard_pass", "DiffGuard PASS record exists."),
    HighRiskPrerequisite("physics_guard_pass", "PhysicsGuard PASS record exists."),
    HighRiskPrerequisite("mcpguard_pass", "MCPGuard PASS record exists where model conditions or INP patches may be affected."),
    HighRiskPrerequisite("patch_preview_accepted", "Patch preview has been accepted as a preview artifact, not applied in place."),
    HighRiskPrerequisite("future_human_gate", "Explicit human solver gate approval record would be required in a future stage."),
    HighRiskPrerequisite("solver_command_configured", "Solver command path is configured in project status or config."),
    HighRiskPrerequisite("source_mutation_absent", "No source CAE/INP mutation occurred outside allowed copied artifacts."),
)

QUEUE_JOB_PREREQUISITES = (
    HighRiskPrerequisite("solver_readiness_design", "Controlled solver readiness design has been accepted."),
    HighRiskPrerequisite("job_manifest_exists", "Task or job manifest exists."),
    HighRiskPrerequisite("future_queue_gate", "Queue mutation gate is approved in a future explicit stage."),
    HighRiskPrerequisite("queue_json_risk_acknowledged", "queue.json write risk is acknowledged."),
    HighRiskPrerequisite("runtime_status_isolation", "Runtime status isolation is defined."),
)

OPEN_ODB_FOR_DIAGNOSIS_PREREQUISITES = (
    HighRiskPrerequisite("odb_under_allowed_artifact_dir", "ODB path exists under an allowed run artifact directory."),
    HighRiskPrerequisite("controlled_solver_completion_record", "Controlled solver completion record exists."),
    HighRiskPrerequisite("future_odb_acceptance_gate", "ODB acceptance gate is pending or required."),
    HighRiskPrerequisite("read_only_extractor_contract", "Read-only ODB extractor contract exists."),
    HighRiskPrerequisite("no_uncontrolled_interactive_open", "No uncontrolled interactive ODB opening is allowed."),
)

EXTRACT_ODB_METRICS_PREREQUISITES = (
    HighRiskPrerequisite("future_odb_metrics_acceptance", "ODB is accepted for metrics in a future gate."),
    HighRiskPrerequisite("metrics_schema_exists", "Metrics schema exists."),
    HighRiskPrerequisite("extractor_contract_exists", "Extraction script contract exists."),
    HighRiskPrerequisite("metrics_output_target_defined", "Output JSON target is defined."),
    HighRiskPrerequisite("metrics_non_final_until_gated", "Metrics remain non-final until EvidenceReportAgent and PipelineSupervisor gates."),
)

SOURCE_MUTATION_PREREQUISITES = (
    HighRiskPrerequisite("source_mutation_justification", "Explicit source mutation justification exists."),
    HighRiskPrerequisite("backup_freeze_plan", "Backup and freeze plan exists."),
    HighRiskPrerequisite("diff_plan", "Diff plan exists."),
    HighRiskPrerequisite("irreversible_warning", "Irreversible mutation warning is acknowledged."),
    HighRiskPrerequisite("future_human_source_gate", "Human gate approval exists in a future explicit stage."),
)

FINAL_EVIDENCE_PREREQUISITES = (
    HighRiskPrerequisite("all_upstream_traces_complete", "All upstream RUN/HANDOFF/GATE traces are complete."),
    HighRiskPrerequisite("metrics_accepted", "Metrics are accepted through a future metrics gate."),
    HighRiskPrerequisite("final_evidence_ledger_draft", "Final evidence ledger draft is complete."),
    HighRiskPrerequisite("pipeline_supervisor_final_review", "PipelineSupervisor final review is complete."),
    HighRiskPrerequisite("future_final_freeze_stage", "Explicit human approval occurs in a future final freeze stage."),
)

RUNTIME_BRIDGE_PREREQUISITES = (
    HighRiskPrerequisite("future_runtime_bridge_design", "Future explicit runtime bridge design exists."),
    HighRiskPrerequisite("security_boundary", "Security boundary is defined."),
    HighRiskPrerequisite("user_confirmation", "User confirmation is defined."),
    HighRiskPrerequisite("log_trace_policy", "Log and trace policy exists."),
    HighRiskPrerequisite("secret_leakage_controls", "No-secret-leak controls are defined."),
    HighRiskPrerequisite("abort_rollback_policy", "Abort and rollback policy exists."),
)

DELETE_OR_OVERWRITE_PREREQUISITES = (
    HighRiskPrerequisite("historical_artifact_inventory", "Historical artifact inventory exists."),
    HighRiskPrerequisite("retention_policy", "Retention policy and replacement rationale are documented."),
    HighRiskPrerequisite("backup_plan", "Backup plan exists."),
    HighRiskPrerequisite("future_human_destructive_gate", "Human destructive-action gate exists in a future explicit stage."),
)


def get_prerequisites_for_action(action_id: str) -> list[dict[str, object]]:
    mapping = {
        "CONTROLLED_SOLVER_RUN": CONTROLLED_SOLVER_RUN_PREREQUISITES,
        "QUEUE_JOB": QUEUE_JOB_PREREQUISITES,
        "OPEN_ODB_FOR_DIAGNOSIS": OPEN_ODB_FOR_DIAGNOSIS_PREREQUISITES,
        "EXTRACT_ODB_METRICS": EXTRACT_ODB_METRICS_PREREQUISITES,
        "MUTATE_SOURCE_CAE": SOURCE_MUTATION_PREREQUISITES,
        "MUTATE_SOURCE_INP": SOURCE_MUTATION_PREREQUISITES,
        "ACCEPT_METRICS_FOR_EVIDENCE": EXTRACT_ODB_METRICS_PREREQUISITES + FINAL_EVIDENCE_PREREQUISITES,
        "APPROVE_FINAL_EVIDENCE": FINAL_EVIDENCE_PREREQUISITES,
        "FREEZE_FINAL_VERDICT": FINAL_EVIDENCE_PREREQUISITES,
        "DELETE_OR_OVERWRITE_HISTORICAL_ARTIFACT": DELETE_OR_OVERWRITE_PREREQUISITES,
        "RUN_CODEX_FROM_GUI": RUNTIME_BRIDGE_PREREQUISITES,
        "AUTO_SCHEDULE_AGENT": RUNTIME_BRIDGE_PREREQUISITES,
    }
    return [item.to_dict() for item in mapping.get(action_id, ())]
