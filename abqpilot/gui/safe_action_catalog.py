from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ActionCategory = Literal[
    "SAFE_READ_ONLY",
    "SAFE_SCAFFOLD",
    "SAFE_NON_SOLVER_REVALIDATION",
    "SAFE_SUPERVISOR_NON_FINAL",
    "DISABLED_HIGH_RISK",
    "DISABLED_FINAL_EVIDENCE",
]

FinalEvidenceEffect = Literal["NONE", "NON_FINAL_NON_SOLVER_RECORD_ONLY"]


@dataclass(frozen=True)
class GuiActionDefinition:
    action_id: str
    display_name: str
    category: ActionCategory
    allowed: bool
    requires_task_dir: bool
    expected_cli_equivalent: str
    risk_level: str
    final_evidence_effect: FinalEvidenceEffect
    panel: str
    backend_method: str | None = None
    disabled_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SAFE_ACTIONS: tuple[GuiActionDefinition, ...] = (
    GuiActionDefinition(
        action_id="list_pipeline_agents",
        display_name="List Pipeline Agents",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=False,
        expected_cli_equivalent="python -m abqpilot.cli list-pipeline-agents",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Task Workspace",
        backend_method="list_pipeline_agents",
    ),
    GuiActionDefinition(
        action_id="scaffold_pipeline_task",
        display_name="Scaffold Pipeline Task",
        category="SAFE_SCAFFOLD",
        allowed=True,
        requires_task_dir=False,
        expected_cli_equivalent="python -m abqpilot.cli scaffold-pipeline-task --task-id <task_id>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Task Workspace",
        backend_method="scaffold_pipeline_task",
    ),
    GuiActionDefinition(
        action_id="list_acom_templates",
        display_name="List ACOM Templates",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=False,
        expected_cli_equivalent="python -m abqpilot.cli list-acom-templates",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="ACOM Handoff",
        backend_method="list_acom_templates",
    ),
    GuiActionDefinition(
        action_id="describe_acom_template",
        display_name="Describe ACOM Template",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=False,
        expected_cli_equivalent="python -m abqpilot.cli describe-acom-template --template-id <template_id>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="ACOM Handoff",
        backend_method="describe_acom_template",
    ),
    GuiActionDefinition(
        action_id="generate_pipeline_acom_handoff",
        display_name="Generate Pipeline ACOM Handoff",
        category="SAFE_SCAFFOLD",
        allowed=True,
        requires_task_dir=False,
        expected_cli_equivalent="python -m abqpilot.cli generate-codex-handoff --task-id <task_id> --template-id <template_id>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="ACOM Handoff",
        backend_method="generate_pipeline_acom_handoff",
    ),
    GuiActionDefinition(
        action_id="validate_acom_template_pack",
        display_name="Validate ACOM Template Pack",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=False,
        expected_cli_equivalent="python -m abqpilot.cli validate-acom-template-pack",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="ACOM Handoff",
        backend_method="validate_acom_template_pack",
    ),
    GuiActionDefinition(
        action_id="intake_acom_result",
        display_name="Intake ACOM Result",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli intake-codex-result --handoff-dir <handoff_dir> --result-json <structured_result.json>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="ACOM Result Intake",
        backend_method="intake_acom_result",
    ),
    GuiActionDefinition(
        action_id="report_acom_result_intake",
        display_name="Report ACOM Result Intake",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-acom-result-intake --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="ACOM Result Intake",
        backend_method="report_acom_result_intake",
    ),
    GuiActionDefinition(
        action_id="scaffold_acom_revalidation",
        display_name="Scaffold ACOM Revalidation",
        category="SAFE_SCAFFOLD",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli scaffold-acom-revalidation --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Downstream Revalidation",
        backend_method="scaffold_acom_revalidation",
    ),
    GuiActionDefinition(
        action_id="report_acom_revalidation",
        display_name="Report ACOM Revalidation",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-acom-revalidation --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Downstream Revalidation",
        backend_method="report_acom_revalidation",
    ),
    GuiActionDefinition(
        action_id="execute_non_solver_revalidation",
        display_name="Execute Non-Solver Revalidation",
        category="SAFE_NON_SOLVER_REVALIDATION",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli execute-non-solver-revalidation --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Non-Solver Revalidation Execution",
        backend_method="execute_non_solver_revalidation",
    ),
    GuiActionDefinition(
        action_id="report_non_solver_revalidation",
        display_name="Report Non-Solver Revalidation",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-non-solver-revalidation --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Non-Solver Revalidation Execution",
        backend_method="report_non_solver_revalidation",
    ),
    GuiActionDefinition(
        action_id="supervisor_review_non_solver_revalidation",
        display_name="Supervisor Review Non-Solver Revalidation",
        category="SAFE_SUPERVISOR_NON_FINAL",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli supervisor-review-non-solver-revalidation --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        panel="PipelineSupervisor Review",
        backend_method="supervisor_review_non_solver_revalidation",
    ),
    GuiActionDefinition(
        action_id="report_supervisor_non_solver_review",
        display_name="Report Supervisor Non-Solver Review",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-supervisor-non-solver-review --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="PipelineSupervisor Review",
        backend_method="report_supervisor_non_solver_review",
    ),
    GuiActionDefinition(
        action_id="generate_non_solver_evidence_summary",
        display_name="Generate Non-Solver Evidence Summary",
        category="SAFE_SUPERVISOR_NON_FINAL",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli generate-non-solver-evidence-summary --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        panel="EvidenceReportAgent Non-Solver Summary",
        backend_method="generate_non_solver_evidence_summary",
    ),
    GuiActionDefinition(
        action_id="report_non_solver_evidence_summary",
        display_name="Report Non-Solver Evidence Summary",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-non-solver-evidence-summary --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="EvidenceReportAgent Non-Solver Summary",
        backend_method="report_non_solver_evidence_summary",
    ),
    GuiActionDefinition(
        action_id="supervisor_ack_non_solver_summary",
        display_name="Supervisor Ack Non-Solver Summary",
        category="SAFE_SUPERVISOR_NON_FINAL",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli supervisor-ack-non-solver-summary --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NON_FINAL_NON_SOLVER_RECORD_ONLY",
        panel="PipelineSupervisor Summary Ack",
        backend_method="supervisor_ack_non_solver_summary",
    ),
    GuiActionDefinition(
        action_id="report_supervisor_non_solver_summary_ack",
        display_name="Report Supervisor Non-Solver Summary Ack",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-supervisor-non-solver-summary-ack --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="PipelineSupervisor Summary Ack",
        backend_method="report_supervisor_non_solver_summary_ack",
    ),
    GuiActionDefinition(
        action_id="validate_pipeline_protocol",
        display_name="Validate Pipeline Protocol",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli validate-pipeline-protocol --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Pipeline Trace",
        backend_method="validate_pipeline_protocol",
    ),
    GuiActionDefinition(
        action_id="report_pipeline_protocol",
        display_name="Report Pipeline Protocol",
        category="SAFE_READ_ONLY",
        allowed=True,
        requires_task_dir=True,
        expected_cli_equivalent="python -m abqpilot.cli report-pipeline-protocol --task-dir <task_dir>",
        risk_level="LOW",
        final_evidence_effect="NONE",
        panel="Pipeline Trace",
        backend_method="report_pipeline_protocol",
    ),
)


DISABLED_ACTIONS: tuple[GuiActionDefinition, ...] = (
    GuiActionDefinition(
        action_id="run_solver_disabled",
        display_name="Run Solver [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Solver execution is unavailable in Stage 5.1A GUI information architecture.",
    ),
    GuiActionDefinition(
        action_id="open_odb_disabled",
        display_name="Open ODB [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="ODB access remains limited to gated extractor paths outside this GUI stage.",
    ),
    GuiActionDefinition(
        action_id="queue_job_disabled",
        display_name="Queue Job [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Queue submission and external queue-worker launch are disabled in Stage 5.1A.",
    ),
    GuiActionDefinition(
        action_id="run_codex_disabled",
        display_name="Run Codex [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="ACOM handoffs are generated only; Codex CLI is not called by AbqPilot.",
    ),
    GuiActionDefinition(
        action_id="auto_schedule_agent_disabled",
        display_name="Auto Schedule Agent [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Automatic multi-agent scheduling is outside Stage 5.1A authority.",
    ),
    GuiActionDefinition(
        action_id="approve_final_evidence_disabled",
        display_name="Approve Final Evidence [DISABLED]",
        category="DISABLED_FINAL_EVIDENCE",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Non-solver acknowledgement is not final evidence approval.",
    ),
    GuiActionDefinition(
        action_id="freeze_final_verdict_disabled",
        display_name="Freeze Final Verdict [DISABLED]",
        category="DISABLED_FINAL_EVIDENCE",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Final verdict freeze is locked unless a later explicit stage changes it.",
    ),
    GuiActionDefinition(
        action_id="approve_solver_odb_metrics_disabled",
        display_name="Approve Solver / ODB / Metrics [DISABLED]",
        category="DISABLED_FINAL_EVIDENCE",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.1A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Solver, ODB, and metrics approval are unavailable in this non-solver GUI stage.",
    ),
    GuiActionDefinition(
        action_id="extract_odb_metrics_disabled",
        display_name="Extract ODB Metrics [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.2A GUI",
        risk_level="HIGH",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="ODB metrics extraction requires a future explicit ODB/metrics gate.",
    ),
    GuiActionDefinition(
        action_id="mutate_source_cae_disabled",
        display_name="Mutate Source CAE [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.2A GUI",
        risk_level="CRITICAL",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Source CAE mutation is locked until a future explicit source-mutation gate.",
    ),
    GuiActionDefinition(
        action_id="mutate_source_inp_disabled",
        display_name="Mutate Source INP [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.2A GUI",
        risk_level="CRITICAL",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Source INP mutation is locked until a future explicit source-mutation gate.",
    ),
    GuiActionDefinition(
        action_id="accept_metrics_for_evidence_disabled",
        display_name="Accept Metrics for Evidence [DISABLED]",
        category="DISABLED_FINAL_EVIDENCE",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.2A GUI",
        risk_level="CRITICAL",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Metrics cannot become evidence without a future explicit evidence gate.",
    ),
    GuiActionDefinition(
        action_id="delete_or_overwrite_historical_artifact_disabled",
        display_name="Delete or Overwrite Historical Artifact [DISABLED]",
        category="DISABLED_HIGH_RISK",
        allowed=False,
        requires_task_dir=False,
        expected_cli_equivalent="not available in Stage 5.2A GUI",
        risk_level="CRITICAL",
        final_evidence_effect="NONE",
        panel="Disabled High-Risk Actions",
        disabled_reason="Destructive historical artifact actions require a future explicit destructive-action gate.",
    ),
)


def get_safe_action_catalog() -> list[dict[str, object]]:
    return [action.to_dict() for action in (*SAFE_ACTIONS, *DISABLED_ACTIONS)]


def get_disabled_high_risk_actions() -> list[dict[str, object]]:
    return [action.to_dict() for action in DISABLED_ACTIONS]


def group_actions_by_panel() -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for action in get_safe_action_catalog():
        grouped.setdefault(str(action["panel"]), []).append(action)
    return grouped


def assert_catalog_safety() -> None:
    for action in (*SAFE_ACTIONS, *DISABLED_ACTIONS):
        if action.final_evidence_effect not in {"NONE", "NON_FINAL_NON_SOLVER_RECORD_ONLY"}:
            raise ValueError(f"unsafe final evidence effect: {action.action_id}")
        if not action.allowed and action.backend_method is not None:
            raise ValueError(f"disabled action has backend: {action.action_id}")
