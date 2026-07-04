from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot import cli
from abqpilot.reporting.run_report import export_run_report
from abqpilot.ui_state.view_model import build_task_view_model


def load_view_model(task_dir: str | Path) -> dict[str, Any]:
    return build_task_view_model(task_dir)


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
