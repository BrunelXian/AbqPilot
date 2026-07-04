from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.pipeline_protocol.agent_registry import agent_names
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


def generate_protocol_report(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    validation = validate_task_protocol(task)
    report_path = task / "PIPELINE_PROTOCOL_REPORT.md"
    text = _render_report(task, validation)
    task.mkdir(parents=True, exist_ok=True)
    report_path.write_text(text, encoding="utf-8")
    return {
        "command": "report-pipeline-protocol",
        "verdict": "PIPELINE_PROTOCOL_REPORT_READY" if validation["success"] else "PIPELINE_PROTOCOL_REPORT_READY_WITH_VALIDATION_ERRORS",
        "success": True,
        "task_dir": str(task),
        "report_path": str(report_path),
        "validation_verdict": validation["verdict"],
        "errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
    }


def _render_report(task: Path, validation: dict[str, Any]) -> str:
    agents = "\n".join(f"- {name}" for name in agent_names())
    errors = "\n".join(f"- {item}" for item in validation.get("errors", [])) or "- none"
    warnings = "\n".join(f"- {item}" for item in validation.get("warnings", [])) or "- none"
    return f"""# Pipeline Protocol Report

## Task Directory
{task}

## Validation Verdict
{validation["verdict"]}

## Pipeline Agents
{agents}

## Trace Protocol
- RUN_XXX.md files are flat Markdown trace files.
- HANDOFF_XXX.md files are station-to-station input contracts.
- GATE_XXX.md files are high-risk transition decisions.

## Errors
{errors}

## Warnings
{warnings}

## Safety Boundary
This report is protocol-only. It does not run solvers, open ODB files, enqueue jobs, call Codex, or schedule agents.
"""
