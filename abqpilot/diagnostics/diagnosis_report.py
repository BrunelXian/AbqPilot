from __future__ import annotations

from typing import Any


def render_diagnosis_summary(result: dict[str, Any]) -> str:
    evidence = result.get("evidence", {})
    lines = [
        "# Abaqus Job / ODB Failure Diagnosis",
        "",
        f"Diagnosis status: `{result.get('diagnosis_status')}`",
        f"Failure category: `{result.get('failure_category')}`",
        f"ODB acceptable for metrics: `{result.get('odb_acceptable_for_metrics')}`",
        f"Recommended next action: {result.get('recommended_next_action')}",
        "",
        "## Evidence",
        "",
        f"- ODB exists: `{evidence.get('odb_exists')}`",
        f"- ODB size bytes: `{evidence.get('odb_size_bytes')}`",
        f"- Lock exists: `{evidence.get('lock_exists')}`",
        f"- Analysis completed: `{evidence.get('analysis_completed')}`",
        f"- Analysis not completed: `{evidence.get('analysis_not_completed')}`",
        f"- Too many attempts: `{evidence.get('too_many_attempts')}`",
        f"- Terminated due to errors: `{evidence.get('terminated_due_to_errors')}`",
        f"- Error lines found: `{evidence.get('error_lines_found')}`",
        "",
        "## Important Lines",
        "",
    ]
    important = result.get("important_lines", {})
    for key in ["dat_error_lines", "msg_error_lines", "log_error_lines"]:
        values = important.get(key) or []
        if values:
            lines.append(f"### {key}")
            lines.extend(f"- `{line}`" for line in values[:12])
            lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "- ODB was not opened directly.",
            "- Solver was not submitted by diagnosis.",
            "- External queue worker was not launched.",
            "- LLM was not used.",
        ]
    )
    return "\n".join(lines) + "\n"

