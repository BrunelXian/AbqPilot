from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.ui_state.view_model import build_task_view_model


def export_run_report(task_dir: str | Path, out_dir: str | Path | None = None) -> dict[str, Any]:
    task = Path(task_dir)
    target = Path(out_dir) if out_dir is not None else task / "reports"
    target.mkdir(parents=True, exist_ok=True)
    view = build_task_view_model(task)
    report = {
        "task_id": view.get("task_id"),
        "overall_status": view.get("overall_status"),
        "pipeline_steps": _step_table(task),
        "modules": view.get("modules", []),
        "important_artifacts": view.get("artifacts", []),
        "jobpilot_status": _read_artifact(task, "abqjobpilot_status_summary"),
        "queue_only_proof": _read_artifact(task, "abqjobpilot_real_enqueue_result"),
        "odb_metrics_summary": _read_artifact(task, "odb_metrics_json"),
        "evaluation": _read_artifact(task, "evaluation_json"),
        "repair_plan": _read_artifact(task, "repair_plan_json"),
        "safety_boundary_summary": {
            "abaqus_solver_submit": "not automatic",
            "queue_runner_launch": "not automatic",
            "abqjobpilot_gui": "not used",
            "openai_api": "not integrated",
            "odb_open": "gated extractor only",
            "real_enqueue": "approval-token gated",
        },
    }
    json_path = target / "ABQPILOT_RUN_REPORT.json"
    md_path = target / "ABQPILOT_RUN_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return {
        "command": "export-run-report",
        "verdict": "RUN_REPORT_EXPORTED",
        "success": True,
        "output_paths": {"run_report_json": str(json_path), "run_report_md": str(md_path)},
        "details": report,
        "warnings": [],
        "errors": [],
    }


def _step_table(task: Path) -> list[dict[str, Any]]:
    state_path = task / "task_state.json"
    if not state_path.exists():
        return []
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return [
        {"step": step, "status": payload.get("status"), "verdict": payload.get("verdict")}
        for step, payload in state.get("steps", {}).items()
    ]


def _read_artifact(task: Path, name: str) -> dict[str, Any] | None:
    artifacts_path = task / "artifacts.json"
    if not artifacts_path.exists():
        return None
    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8")).get("artifacts", [])
    for item in artifacts:
        if item.get("name") != name:
            continue
        path = Path(item.get("path", ""))
        if path.exists() and path.suffix.lower() == ".json":
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {"path": str(path), "parse_error": True}
        return {"path": str(path), "exists": path.exists()}
    return None


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AbqPilot Run Report",
        "",
        f"Task ID: `{report.get('task_id')}`",
        f"Overall status: `{report.get('overall_status')}`",
        "",
        "## Pipeline Steps",
        "",
        "| Step | Status | Verdict |",
        "| --- | --- | --- |",
    ]
    for step in report.get("pipeline_steps", []):
        lines.append(f"| {step.get('step')} | {step.get('status')} | {step.get('verdict')} |")
    lines.extend(["", "## Module Status", "", "| Module | Status | Last Message |", "| --- | --- | --- |"])
    for module in report.get("modules", []):
        lines.append(f"| {module.get('display_name')} | {module.get('status')} | {module.get('last_message')} |")
    lines.extend(["", "## Safety Boundary Summary", ""])
    for key, value in report.get("safety_boundary_summary", {}).items():
        lines.append(f"- {key}: {value}")
    jobpilot = report.get("jobpilot_status") or {}
    if jobpilot:
        lines.extend(
            [
                "",
                "## JobPilot Status",
                "",
                f"- Job ID: `{jobpilot.get('job_id')}`",
                f"- Normalized status: `{jobpilot.get('normalized_status')}`",
                f"- Expected ODB: `{jobpilot.get('expected_odb_path')}`",
            ]
        )
    repair = report.get("repair_plan") or {}
    if repair:
        lines.extend(["", "## Repair Plan", "", f"- Verdict: `{repair.get('evaluation_verdict')}`"])
    return "\n".join(lines) + "\n"
