from __future__ import annotations

from typing import Any


MODULE_DEFINITIONS = [
    ("01_export_cae", "cae_export", "CAE Export", "2.0"),
    ("02_audit_heat_x2", "heat_patch_audit", "Heat Patch Audit", "2.0"),
    ("02_audit_heat_x2", "static_validation", "Static Validation", "2.0"),
    ("02_audit_heat_x2", "diff_guard", "Diff Guard", "2.0"),
    ("02_audit_heat_x2", "physics_guard", "Physics Guard", "2.0"),
    ("03_abqjobpilot_preflight", "jobpilot_preflight", "JobPilot Preflight", "2.3"),
    ("04_abqjobpilot_dry_run_enqueue", "jobpilot_dry_run_enqueue", "JobPilot Dry-Run Enqueue", "2.4"),
    ("05_jobpilot_enqueue_authorization", "human_approval", "Human Approval", "2.5"),
    ("06_abqjobpilot_real_enqueue", "real_queue_enqueue", "Real Queue Enqueue", "2.6"),
    ("07_abqjobpilot_status_poll", "status_poll", "Status Poll", "2.7"),
    ("08_solver_intake", "solver_intake", "Solver Intake", "2.8"),
    ("09_odb_metrics", "odb_metrics", "ODB Metrics", "2.8"),
    ("10_compare_metrics", "metrics_comparison", "Metrics Comparison", "2.9"),
    ("stage2_9_evaluation", "evaluation", "Evaluation", "2.9"),
    ("stage2_9_repair_plan", "repair_plan", "Repair Plan", "2.9"),
    ("gui", "gui", "GUI", "3.1"),
]


STATUS_MAP = {
    "PENDING": "PENDING",
    "RUNNING": "RUNNING",
    "COMPLETED": "COMPLETED",
    "SKIPPED": "SKIPPED",
    "FAILED": "FAILED",
    "WAITING_FOR_MANUAL_ACTION": "WAITING",
    "STOPPED_BY_MODE_LIMIT": "BLOCKED",
}


def build_module_registry(task_state: dict[str, Any] | None = None, artifacts: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    task_state = task_state or {}
    artifacts = artifacts or {}
    steps = task_state.get("steps", {})
    artifact_items = artifacts.get("artifacts", [])
    modules = []
    for step_name, module_id, display_name, stage in MODULE_DEFINITIONS:
        step = steps.get(step_name, {})
        last_artifact = _last_artifact_for_step(artifact_items, step_name)
        modules.append(
            {
                "module_id": module_id,
                "display_name": display_name,
                "stage": stage,
                "status": STATUS_MAP.get(step.get("status"), "PENDING"),
                "current_task": task_state.get("task_id"),
                "last_artifact": last_artifact,
                "last_message": step.get("verdict"),
                "started_at": step.get("started_at"),
                "finished_at": step.get("finished_at"),
                "duration_seconds": None,
                "step_name": step_name,
            }
        )
    return modules


def module_id_for_step(step_name: str | None) -> str | None:
    for known_step, module_id, _display, _stage in MODULE_DEFINITIONS:
        if known_step == step_name:
            return module_id
    return None


def _last_artifact_for_step(artifacts: list[dict[str, Any]], step_name: str) -> str | None:
    for artifact in reversed(artifacts):
        if artifact.get("producer_step") == step_name:
            return artifact.get("path")
    return None
