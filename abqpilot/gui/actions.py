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
