from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.pipeline_protocol.frontmatter import validate_frontmatter
from abqpilot.pipeline_protocol.task_scaffold import GATES, HANDOFFS, RUNS


def validate_task_protocol(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    errors: list[str] = []
    warnings: list[str] = []
    if not task.exists():
        errors.append(f"task directory missing: {task}")
        return _result(task, errors, warnings)
    required_files = [
        task / "TASK_PLAN.md",
        task / "TRACE_INDEX.md",
        task / "TASK_FINAL_EVIDENCE_LEDGER.md",
    ]
    required_files.extend(task / "trace" / f"{run_id}_{name}.md" for run_id, name, *_rest in RUNS)
    required_files.extend(task / "handoffs" / f"{handoff_id}_{name}.md" for handoff_id, name, *_rest in HANDOFFS)
    required_files.extend(task / "gates" / f"{gate_id}_{name}.md" for gate_id, name, *_rest in GATES)
    for path in required_files:
        if not path.exists():
            errors.append(f"missing required file: {path}")
            continue
        frontmatter_result = validate_frontmatter(path)
        if not frontmatter_result["valid"]:
            errors.extend(f"{path}: {error}" for error in frontmatter_result["errors"])
    trace_dir = task / "trace"
    if trace_dir.exists():
        for child in trace_dir.iterdir():
            if child.is_dir():
                errors.append(f"trace must be flat Markdown files only; found directory: {child}")
            elif child.suffix.lower() != ".md":
                warnings.append(f"non-Markdown trace entry ignored: {child}")
    for run_id, name, *_rest in RUNS:
        artifact_dir = task / "artifacts" / f"{run_id.lower()}_{name.lower()}"
        if not artifact_dir.exists():
            errors.append(f"missing artifact directory: {artifact_dir}")
    return _result(task, errors, warnings)


def _result(task: Path, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "command": "validate-pipeline-protocol",
        "verdict": "PIPELINE_PROTOCOL_VALID" if not errors else "PIPELINE_PROTOCOL_INVALID",
        "success": not errors,
        "task_dir": str(task),
        "errors": errors,
        "warnings": warnings,
    }
