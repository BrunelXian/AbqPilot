from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot import cli
from abqpilot.gui.beta_smoke import build_gui_beta_e2e_smoke, write_gui_beta_e2e_smoke_outputs
from abqpilot.gui.controlled_solver_active_gate_card import build_controlled_solver_active_gate_card
from abqpilot.gui.controlled_solver_active_gate_fixture_report import write_active_gate_writer_fixture_report
from abqpilot.gui.controlled_solver_active_gate_schema import (
    build_controlled_solver_active_gate_schema,
    write_controlled_solver_active_gate_design,
)
from abqpilot.gui.controlled_solver_execution_handoff_card import build_controlled_solver_execution_handoff_card
from abqpilot.gui.controlled_solver_execution_handoff_draft import create_controlled_solver_execution_handoff_draft_no_exec
from abqpilot.gui.controlled_solver_dry_run_request_card import build_controlled_solver_dry_run_request_card
from abqpilot.gui.controlled_solver_dry_run_request import create_controlled_solver_dry_run_request_no_exec
from abqpilot.gui.controlled_solver_demo_smoke_card import build_controlled_solver_demo_smoke_card
from abqpilot.gui.controlled_solver_demo_smoke_v2_card import build_controlled_solver_demo_smoke_v2_card
from abqpilot.gui.controlled_solver_demo_smoke import run_controlled_solver_demo_smoke
from abqpilot.gui.controlled_solver_demo_smoke_v2 import run_controlled_solver_demo_smoke_v2
from abqpilot.gui.controlled_solver_request_card import build_controlled_solver_request_card
from abqpilot.gui.controlled_solver_request_draft import create_controlled_solver_request_draft_no_exec
from abqpilot.gui.controlled_solver_request_preflight_card import build_controlled_solver_request_preflight_card
from abqpilot.gui.controlled_solver_request_preflight import create_controlled_solver_request_preflight_no_exec
from abqpilot.gui.controlled_solver_real_gate_card import build_controlled_solver_real_gate_card
from abqpilot.gui.controlled_solver_real_gate_creation import create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_inactive_gate_card import build_controlled_solver_inactive_gate_card
from abqpilot.gui.controlled_solver_inactive_gate_draft import (
    build_controlled_solver_inactive_gate_draft,
    write_controlled_solver_inactive_gate_draft,
)
from abqpilot.gui.controlled_solver_gate_card import build_controlled_solver_gate_card
from abqpilot.gui.controlled_solver_gate_preview import build_controlled_solver_gate_preview, write_controlled_solver_gate_preview
from abqpilot.gui.high_risk_gate_catalog import get_high_risk_gate_catalog
from abqpilot.gui.high_risk_gate_preview import build_high_risk_gate_ux_spec, write_high_risk_gate_ux_spec
from abqpilot.gui.high_risk_gate_ux import build_high_risk_gate_ux
from abqpilot.gui.layout_sections import build_layout_sections
from abqpilot.gui.next_step_recommender import build_next_step_recommendation
from abqpilot.gui.recommendation_cards import build_next_step_recommendation_card
from abqpilot.gui.safe_action_catalog import get_safe_action_catalog, group_actions_by_panel
from abqpilot.gui.timeline_interaction import select_timeline_step
from abqpilot.gui.trace_detail_cards import build_trace_detail_card
from abqpilot.gui.trace_viewer import build_trace_viewer
from abqpilot.gui.workflow_presenter import build_gui_workflow_presenter
from abqpilot.gui.workflow_state import inspect_gui_workflow_state
from abqpilot.reporting.run_report import export_run_report
from abqpilot.ui_state.view_model import build_task_view_model


def load_view_model(task_dir: str | Path) -> dict[str, Any]:
    return build_task_view_model(task_dir)


def load_workflow_state(task_dir: str | Path | None) -> dict[str, Any]:
    return inspect_gui_workflow_state(task_dir)


def load_workflow_presenter(task_dir: str | Path | None, project_root: str | Path | None = None) -> dict[str, Any]:
    return build_gui_workflow_presenter(task_dir, project_root=project_root)


def load_safe_action_catalog() -> dict[str, Any]:
    return {"actions": get_safe_action_catalog(), "panels": group_actions_by_panel()}


def load_layout_sections(task_dir: str | Path | None, project_root: str | Path | None = None) -> dict[str, Any]:
    return build_layout_sections(task_dir, project_root=project_root)


def load_gui_beta_smoke(project_root: str | Path, task_dir: str | Path | None = None) -> dict[str, Any]:
    return build_gui_beta_e2e_smoke(project_root, task_dir=task_dir)


def report_gui_beta_smoke(project_root: str | Path, task_dir: str | Path | None = None) -> dict[str, Any]:
    return write_gui_beta_e2e_smoke_outputs(project_root, task_dir=task_dir)


def load_high_risk_gate_catalog() -> dict[str, Any]:
    return {"actions": get_high_risk_gate_catalog()}


def load_high_risk_gate_preview(action_id: str) -> dict[str, Any]:
    return build_high_risk_gate_ux(action_id)


def load_high_risk_gate_ux_spec(project_root: str | Path) -> dict[str, Any]:
    return build_high_risk_gate_ux_spec(project_root)


def report_high_risk_gate_ux_spec(project_root: str | Path) -> dict[str, Any]:
    return write_high_risk_gate_ux_spec(project_root)


def load_controlled_solver_gate_preview(task_dir: str | Path | None = None, candidate_inp: str | Path | None = None) -> dict[str, Any]:
    return build_controlled_solver_gate_preview(task_dir=task_dir, candidate_inp=candidate_inp)


def load_controlled_solver_gate_card(task_dir: str | Path | None = None, candidate_inp: str | Path | None = None) -> dict[str, Any]:
    return build_controlled_solver_gate_card(task_dir=task_dir, candidate_inp=candidate_inp)


def report_controlled_solver_gate_preview(
    project_root: str | Path,
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
) -> dict[str, Any]:
    return write_controlled_solver_gate_preview(project_root=project_root, task_dir=task_dir, candidate_inp=candidate_inp)


def load_controlled_solver_inactive_gate_draft(task_dir: str | Path | None = None, candidate_inp: str | Path | None = None) -> dict[str, Any]:
    return build_controlled_solver_inactive_gate_draft(task_dir=task_dir, candidate_inp=candidate_inp)


def load_controlled_solver_inactive_gate_card(task_dir: str | Path | None = None, candidate_inp: str | Path | None = None) -> dict[str, Any]:
    return build_controlled_solver_inactive_gate_card(task_dir=task_dir, candidate_inp=candidate_inp)


def report_controlled_solver_inactive_gate_draft(
    project_root: str | Path,
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
) -> dict[str, Any]:
    return write_controlled_solver_inactive_gate_draft(project_root=project_root, task_dir=task_dir, candidate_inp=candidate_inp)


def load_controlled_solver_active_gate_schema(
    task_id: str = "UNSELECTED_TASK",
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    return build_controlled_solver_active_gate_schema(task_id=task_id, task_dir=task_dir, candidate_artifact_path=candidate_artifact_path)


def load_controlled_solver_active_gate_card(
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    return build_controlled_solver_active_gate_card(task_dir=task_dir, candidate_artifact_path=candidate_artifact_path)


def report_controlled_solver_active_gate_design(
    project_root: str | Path,
    task_id: str = "UNSELECTED_TASK",
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    return write_controlled_solver_active_gate_design(
        project_root=project_root,
        task_id=task_id,
        task_dir=task_dir,
        candidate_artifact_path=candidate_artifact_path,
    )


def report_controlled_solver_active_gate_writer_policy(project_root: str | Path) -> dict[str, Any]:
    return write_active_gate_writer_fixture_report(project_root)


def load_controlled_solver_real_gate_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_real_gate_card(project_root)


def create_controlled_solver_smoke_gate_no_exec(project_root: str | Path) -> dict[str, Any]:
    return create_controlled_solver_real_gate_smoke(project_root)


def load_controlled_solver_execution_handoff_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_execution_handoff_card(project_root)


def create_controlled_solver_execution_handoff_draft(project_root: str | Path) -> dict[str, Any]:
    return create_controlled_solver_execution_handoff_draft_no_exec(project_root)


def load_controlled_solver_request_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_request_card(project_root)


def create_controlled_solver_request_draft(project_root: str | Path) -> dict[str, Any]:
    return create_controlled_solver_request_draft_no_exec(project_root)


def load_controlled_solver_request_preflight_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_request_preflight_card(project_root)


def create_controlled_solver_request_preflight(project_root: str | Path) -> dict[str, Any]:
    return create_controlled_solver_request_preflight_no_exec(project_root)


def load_controlled_solver_dry_run_request_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_dry_run_request_card(project_root)


def create_controlled_solver_dry_run_request(project_root: str | Path) -> dict[str, Any]:
    return create_controlled_solver_dry_run_request_no_exec(project_root)


def load_controlled_solver_demo_smoke_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_demo_smoke_card(project_root)


def load_controlled_solver_demo_smoke_v2_card(project_root: str | Path) -> dict[str, Any]:
    return build_controlled_solver_demo_smoke_v2_card(project_root)


def run_controlled_solver_demo_smoke_action(project_root: str | Path) -> dict[str, Any]:
    return run_controlled_solver_demo_smoke(project_root, attempt_solver=True)


def load_next_step_recommendation(task_dir: str | Path | None) -> dict[str, Any]:
    return build_next_step_recommendation(task_dir)


def load_next_step_recommendation_card(task_dir: str | Path | None) -> dict[str, Any]:
    return build_next_step_recommendation_card(task_dir)


def load_trace_viewer(task_dir: str | Path | None) -> dict[str, Any]:
    return build_trace_viewer(task_dir)


def load_timeline_step(task_dir: str | Path | None, step_id: str) -> dict[str, Any]:
    return select_timeline_step(task_dir, step_id)


def load_trace_detail_card(task_dir: str | Path | None, step_id: str) -> dict[str, Any]:
    return build_trace_detail_card(task_dir, step_id)


def run_prepare_pipeline(config: str | Path, task_id: str | None = None) -> dict[str, Any]:
    return cli.command_run_sanity_demo(config, mode="prepare-only", task_id=task_id)


def poll_jobpilot_status(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    config = task / "task_config.json"
    return cli.command_run_sanity_demo(config, task_id=task.name, resume=True, poll_jobpilot_status=True)


def continue_from_job_output(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_continue_from_job_output(task_dir)


def generate_repair_plan(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_generate_repair_plan(task_dir=task_dir)


def export_report(task_dir: str | Path) -> dict[str, Any]:
    return export_run_report(task_dir)


def list_pipeline_agents() -> dict[str, Any]:
    return cli.command_list_pipeline_agents()


def scaffold_pipeline_task(task_id: str, root: str | Path | None = None) -> dict[str, Any]:
    return cli.command_scaffold_pipeline_task(task_id=task_id, root=root)


def validate_pipeline_protocol(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_validate_pipeline_protocol(task_dir=task_dir)


def report_pipeline_protocol(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_report_pipeline_protocol(task_dir=task_dir)


def list_acom_templates() -> dict[str, Any]:
    return cli.command_list_acom_templates()


def describe_acom_template(template_id: str) -> dict[str, Any]:
    return cli.command_describe_acom_template(template_id=template_id)


def generate_pipeline_acom_handoff(task_id: str, template_id: str) -> dict[str, Any]:
    return cli.command_generate_codex_handoff(task_id=task_id, template_id=template_id)


def validate_acom_template_pack() -> dict[str, Any]:
    return cli.command_validate_acom_template_pack()


def intake_acom_result(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    return cli.command_intake_codex_result(
        handoff_dir=task / "codex_handoff",
        result_json_path=task / "codex_result" / "structured_result.json",
    )


def report_acom_result_intake(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_report_acom_result_intake(task_dir=task_dir)


def generate_non_solver_evidence_summary(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_generate_non_solver_evidence_summary(task_dir=task_dir)


def report_non_solver_evidence_summary(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_report_non_solver_evidence_summary(task_dir=task_dir)


def supervisor_ack_non_solver_summary(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_supervisor_ack_non_solver_summary(task_dir=task_dir)


def report_supervisor_non_solver_summary_ack(task_dir: str | Path) -> dict[str, Any]:
    return cli.command_report_supervisor_non_solver_summary_ack(task_dir=task_dir)


