from __future__ import annotations

from pathlib import Path
from typing import Any


ARTIFACT_PATTERNS: dict[str, tuple[str, ...]] = {
    "acom_handoff": (
        "codex_handoff/handoff_manifest.json",
        "codex_handoff/codex_task.md",
        "codex_handoff/input_manifest.json",
    ),
    "acom_result_intake": (
        "codex_result/structured_result.json",
        "codex_result/acom_result_intake.json",
        "codex_result/acom_result_intake_report.md",
    ),
    "revalidation_scaffold": ("revalidation/*/REVALIDATION_SCAFFOLD.json",),
    "non_solver_revalidation": (
        "revalidation/*/REVALIDATION_EXECUTION_RESULT.json",
        "revalidation/*/REVALIDATION_EXECUTION_REPORT.md",
    ),
    "supervisor_review": (
        "supervisor_review/SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json",
        "supervisor_review/SUPERVISOR_NON_SOLVER_REVIEW_REPORT.md",
    ),
    "non_solver_ledger": (
        "NON_SOLVER_EVIDENCE_LEDGER.json",
        "NON_SOLVER_EVIDENCE_LEDGER.md",
    ),
    "evidence_summary": (
        "evidence_report/NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json",
        "evidence_report/NON_SOLVER_EVIDENCE_SUMMARY_REPORT.md",
    ),
    "supervisor_ack": (
        "supervisor_summary_ack/SUPERVISOR_NON_SOLVER_SUMMARY_ACK_RESULT.json",
        "supervisor_summary_ack/SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REPORT.md",
        "NON_SOLVER_SUMMARY_ACK_LEDGER.json",
        "NON_SOLVER_SUMMARY_ACK_LEDGER.md",
    ),
}


def resolve_evidence_files(task_dir: str | Path, step_id: str | None = None) -> dict[str, Any]:
    task = Path(task_dir)
    selected = [step_id] if step_id else list(ARTIFACT_PATTERNS)
    resolved: dict[str, Any] = {}
    for key in selected:
        files: list[str] = []
        missing: list[str] = []
        for pattern in ARTIFACT_PATTERNS.get(key, ()):
            matches = sorted(task.glob(pattern))
            if matches:
                files.extend(str(path) for path in matches)
            else:
                missing.append(pattern)
        resolved[key] = {
            "files": files,
            "json_files": [path for path in files if path.lower().endswith(".json")],
            "markdown_files": [path for path in files if path.lower().endswith(".md")],
            "missing": missing,
        }
    return resolved


def common_artifact_locations(task_dir: str | Path) -> dict[str, str]:
    task = Path(task_dir)
    return {
        "handoff_manifest": str(task / "codex_handoff" / "handoff_manifest.json"),
        "structured_result": str(task / "codex_result" / "structured_result.json"),
        "acom_result_intake": str(task / "codex_result" / "acom_result_intake.json"),
        "supervisor_review": str(task / "supervisor_review" / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json"),
        "non_solver_ledger": str(task / "NON_SOLVER_EVIDENCE_LEDGER.json"),
        "evidence_summary": str(task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"),
        "supervisor_summary_ack": str(task / "supervisor_summary_ack" / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_RESULT.json"),
        "summary_ack_ledger": str(task / "NON_SOLVER_SUMMARY_ACK_LEDGER.json"),
    }
