from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from abqpilot.gui.high_risk_prerequisites import get_prerequisites_for_action


HighRiskLevel = Literal["HIGH", "CRITICAL"]
HighRiskFinalEvidenceEffect = Literal["NONE", "PREVIEW_ONLY", "FUTURE_STAGE_REQUIRED"]

FORBIDDEN_FINAL_EFFECTS = {
    "FINAL_EVIDENCE_APPROVAL",
    "FINAL_VERDICT_FREEZE",
    "SOLVER_APPROVAL",
    "ODB_ACCEPTANCE",
    "METRICS_APPROVAL",
}


@dataclass(frozen=True)
class HighRiskGateAction:
    action_id: str
    display_name: str
    risk_level: HighRiskLevel
    disabled_reason: str
    risk_summary: str
    possible_failure_modes: tuple[str, ...]
    required_evidence_inputs: tuple[str, ...]
    expected_future_outputs: tuple[str, ...]
    forbidden_without_gate: tuple[str, ...]
    user_warning_copy: str
    required_confirmation_copy: str
    final_evidence_effect: HighRiskFinalEvidenceEffect = "FUTURE_STAGE_REQUIRED"
    default_allowed: bool = False
    executable_in_stage_5_2a: bool = False
    requires_human_gate: bool = True
    requires_future_stage: bool = True
    preview_only: bool = True

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["required_prerequisites"] = get_prerequisites_for_action(self.action_id)
        return data


HIGH_RISK_ACTIONS: tuple[HighRiskGateAction, ...] = (
    HighRiskGateAction(
        action_id="CONTROLLED_SOLVER_RUN",
        display_name="Controlled Solver Run",
        risk_level="HIGH",
        disabled_reason="Solver execution requires a future explicit human gate and fixed command approval.",
        risk_summary="Runs Abaqus and may create solver outputs, locks, or partial ODB files.",
        possible_failure_modes=("solver divergence", "partial ODB", "unexpected runtime output", "resource exhaustion"),
        required_evidence_inputs=("candidate INP", "StaticValidator", "DiffGuard", "PhysicsGuard", "MCPGuard where relevant"),
        expected_future_outputs=("solver approval token", "fixed command preview", "solver run directory", "diagnosis artifact"),
        forbidden_without_gate=("run Abaqus", "submit solver", "create solver request files"),
        user_warning_copy="Controlled solver run is locked. Stage 5.2A shows requirements only and does not run Abaqus.",
        required_confirmation_copy="Future stage must bind candidate hashes, guard results, command preview, expected ODB, and human approval.",
    ),
    HighRiskGateAction(
        action_id="QUEUE_JOB",
        display_name="Queue Job",
        risk_level="HIGH",
        disabled_reason="Queue mutation and queue-worker lifecycle require a future explicit gate.",
        risk_summary="May mutate queue files or trigger external execution lifecycle.",
        possible_failure_modes=("queue.json mutation", "runtime status drift", "duplicate job", "untracked external execution"),
        required_evidence_inputs=("job manifest", "queue mutation gate design", "runtime isolation plan"),
        expected_future_outputs=("queue approval token", "queue mutation report", "runtime status trace"),
        forbidden_without_gate=("enqueue job", "launch queue worker", "mutate queue.json"),
        user_warning_copy="Queue job is locked. Stage 5.2A does not enqueue or mutate runtime queue files.",
        required_confirmation_copy="Future stage must explicitly approve queue mutation and runtime status handling.",
    ),
    HighRiskGateAction(
        action_id="OPEN_ODB_FOR_DIAGNOSIS",
        display_name="Open ODB for Diagnosis",
        risk_level="HIGH",
        disabled_reason="ODB access remains gated and cannot be opened interactively in Stage 5.2A.",
        risk_summary="ODB access can blur diagnostic metadata checks with uncontrolled model database reads.",
        possible_failure_modes=("locked ODB", "partial ODB accepted accidentally", "uncontrolled interactive open"),
        required_evidence_inputs=("ODB path", "solver completion record", "ODB acceptance gate design"),
        expected_future_outputs=("ODB diagnosis report", "acceptability decision", "read-only extractor log"),
        forbidden_without_gate=("open ODB", "launch Abaqus/CAE", "bypass diagnosis"),
        user_warning_copy="ODB opening is locked. Stage 5.2A previews the ODB gate only.",
        required_confirmation_copy="Future stage must prove controlled ODB acceptance before any extractor use.",
    ),
    HighRiskGateAction(
        action_id="EXTRACT_ODB_METRICS",
        display_name="Extract ODB Metrics",
        risk_level="HIGH",
        disabled_reason="Metrics extraction requires future ODB acceptance and metrics gate.",
        risk_summary="Metrics may be mistaken for accepted evidence if extracted before acceptance.",
        possible_failure_modes=("partial metrics", "wrong frame", "unaccepted ODB", "schema drift"),
        required_evidence_inputs=("accepted ODB gate", "metrics schema", "extractor contract"),
        expected_future_outputs=("metrics JSON", "metrics validation report", "comparison report"),
        forbidden_without_gate=("extract metrics", "accept metrics", "update final evidence"),
        user_warning_copy="ODB metrics extraction is locked. Stage 5.2A only shows prerequisites.",
        required_confirmation_copy="Future stage must accept ODB and metric schema before extraction.",
    ),
    HighRiskGateAction(
        action_id="MUTATE_SOURCE_CAE",
        display_name="Mutate Source CAE",
        risk_level="CRITICAL",
        disabled_reason="Source CAE mutation is irreversible-risk work and requires a future explicit source gate.",
        risk_summary="May alter the canonical model source.",
        possible_failure_modes=("lost source intent", "unreviewed model drift", "irreversible overwrite"),
        required_evidence_inputs=("mutation justification", "backup plan", "diff plan"),
        expected_future_outputs=("source mutation approval", "backup artifact", "post-mutation audit"),
        forbidden_without_gate=("edit CAE", "overwrite CAE", "save source CAE"),
        user_warning_copy="Source CAE mutation is locked. Stage 5.2A never mutates source model files.",
        required_confirmation_copy="Future stage must document backup, diff, and explicit human approval.",
    ),
    HighRiskGateAction(
        action_id="MUTATE_SOURCE_INP",
        display_name="Mutate Source INP",
        risk_level="CRITICAL",
        disabled_reason="Source INP mutation must be separated from copied preview artifacts.",
        risk_summary="May destroy traceability between source export and candidates.",
        possible_failure_modes=("unbounded raw edit", "lost source baseline", "unreviewed solver input drift"),
        required_evidence_inputs=("mutation justification", "backup plan", "diff plan"),
        expected_future_outputs=("source mutation approval", "backup artifact", "post-mutation audit"),
        forbidden_without_gate=("edit source INP", "overwrite source INP", "raw unbounded INP edit"),
        user_warning_copy="Source INP mutation is locked. Stage 5.2A never mutates source INP files.",
        required_confirmation_copy="Future stage must document backup, diff, and explicit human approval.",
    ),
    HighRiskGateAction(
        action_id="ACCEPT_METRICS_FOR_EVIDENCE",
        display_name="Accept Metrics for Evidence",
        risk_level="CRITICAL",
        disabled_reason="Metric acceptance can affect final evidence and requires future supervisor gates.",
        risk_summary="May convert computational results into evidence if approved too early.",
        possible_failure_modes=("bad metrics accepted", "unaccepted ODB used", "final evidence contamination"),
        required_evidence_inputs=("metrics JSON", "metrics validation", "comparison report", "ODB acceptance gate"),
        expected_future_outputs=("metrics acceptance gate", "evidence report draft", "supervisor review"),
        forbidden_without_gate=("accept metrics", "update final evidence", "freeze verdict"),
        user_warning_copy="Metrics evidence acceptance is locked. Stage 5.2A does not approve metrics.",
        required_confirmation_copy="Future stage must bind ODB acceptance, metrics validation, and supervisor review.",
    ),
    HighRiskGateAction(
        action_id="APPROVE_FINAL_EVIDENCE",
        display_name="Approve Final Evidence",
        risk_level="CRITICAL",
        disabled_reason="Final evidence approval is outside Stage 5.2A authority.",
        risk_summary="Would convert non-final records into final project evidence.",
        possible_failure_modes=("premature final evidence", "missing upstream trace", "unreviewed metrics"),
        required_evidence_inputs=("complete trace", "accepted metrics", "final evidence ledger draft", "supervisor review"),
        expected_future_outputs=("final evidence approval gate", "final evidence ledger"),
        forbidden_without_gate=("approve final evidence", "update TASK_FINAL_EVIDENCE_LEDGER.md"),
        user_warning_copy="Final evidence remains locked. Stage 5.2A is preview-only.",
        required_confirmation_copy="Future final evidence stage must explicitly approve final evidence.",
    ),
    HighRiskGateAction(
        action_id="FREEZE_FINAL_VERDICT",
        display_name="Freeze Final Verdict",
        risk_level="CRITICAL",
        disabled_reason="Final verdict freeze requires a future explicit final freeze stage.",
        risk_summary="Would make the project verdict final.",
        possible_failure_modes=("premature verdict", "unaccepted evidence", "missing human approval"),
        required_evidence_inputs=("approved final evidence", "PipelineSupervisor final review", "human freeze approval"),
        expected_future_outputs=("final verdict freeze gate", "final status update"),
        forbidden_without_gate=("freeze verdict", "publish final status"),
        user_warning_copy="Final verdict freeze is locked. Stage 5.2A cannot freeze verdicts.",
        required_confirmation_copy="Future explicit final freeze stage must bind all final evidence records.",
    ),
    HighRiskGateAction(
        action_id="DELETE_OR_OVERWRITE_HISTORICAL_ARTIFACT",
        display_name="Delete or Overwrite Historical Artifact",
        risk_level="CRITICAL",
        disabled_reason="Historical artifact deletion/overwrite is destructive and requires a future explicit gate.",
        risk_summary="May destroy traceability and audit history.",
        possible_failure_modes=("lost audit trail", "irreversible deletion", "overwritten evidence"),
        required_evidence_inputs=("artifact inventory", "retention policy", "backup plan"),
        expected_future_outputs=("destructive-action approval gate", "backup record", "retention report"),
        forbidden_without_gate=("delete artifact", "overwrite artifact", "rewrite history"),
        user_warning_copy="Historical artifact deletion/overwrite is locked. Stage 5.2A only previews requirements.",
        required_confirmation_copy="Future destructive-action stage must require explicit human approval.",
    ),
    HighRiskGateAction(
        action_id="RUN_CODEX_FROM_GUI",
        display_name="Run Codex from GUI",
        risk_level="HIGH",
        disabled_reason="ACOM keeps Codex external/manual; GUI Codex execution requires a future runtime bridge design.",
        risk_summary="Would introduce tool execution and security boundary concerns.",
        possible_failure_modes=("unbounded execution", "secret leakage", "trace gaps", "unexpected file mutation"),
        required_evidence_inputs=("runtime bridge design", "security boundary", "trace policy", "secret controls"),
        expected_future_outputs=("runtime bridge gate", "execution trace", "abort/rollback policy"),
        forbidden_without_gate=("call Codex CLI", "auto-execute handoff", "bridge Codex runtime"),
        user_warning_copy="GUI does not call Codex CLI. Codex remains external/manual in Stage 5.2A.",
        required_confirmation_copy="Future runtime bridge stage must prove security, trace, and abort controls.",
    ),
    HighRiskGateAction(
        action_id="AUTO_SCHEDULE_AGENT",
        display_name="Auto Schedule Agent",
        risk_level="HIGH",
        disabled_reason="Automatic scheduling is outside Stage 5.2A and requires a future orchestration design.",
        risk_summary="May execute downstream agents without explicit user control.",
        possible_failure_modes=("unintended agent execution", "high-risk agent run", "trace mismatch", "approval bypass"),
        required_evidence_inputs=("orchestration design", "agent risk policy", "trace policy", "abort/rollback policy"),
        expected_future_outputs=("scheduler gate", "agent execution trace", "supervisor policy"),
        forbidden_without_gate=("auto-schedule agents", "run high-risk agents", "bypass handoff gates"),
        user_warning_copy="Automatic agent scheduling is locked. Stage 5.2A only previews requirements.",
        required_confirmation_copy="Future orchestration stage must define policy, trace, and human controls.",
    ),
)


def get_high_risk_gate_catalog() -> list[dict[str, object]]:
    return [action.to_dict() for action in HIGH_RISK_ACTIONS]


def get_high_risk_action(action_id: str) -> dict[str, object]:
    for action in HIGH_RISK_ACTIONS:
        if action.action_id == action_id:
            return action.to_dict()
    raise KeyError(f"unknown high-risk action: {action_id}")


def assert_high_risk_catalog_safety() -> None:
    for action in HIGH_RISK_ACTIONS:
        if action.default_allowed:
            raise ValueError(f"default allowed high-risk action: {action.action_id}")
        if action.executable_in_stage_5_2a:
            raise ValueError(f"executable Stage 5.2A action: {action.action_id}")
        if not action.preview_only:
            raise ValueError(f"non-preview high-risk action: {action.action_id}")
        if not action.requires_human_gate:
            raise ValueError(f"missing human gate requirement: {action.action_id}")
        if action.final_evidence_effect in FORBIDDEN_FINAL_EFFECTS:
            raise ValueError(f"forbidden final evidence effect: {action.action_id}")
