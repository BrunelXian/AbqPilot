from __future__ import annotations

from pathlib import Path
from typing import Any


ARTIFACT_TYPES = (
    "RUN_REPORT",
    "HANDOFF",
    "GATE_DECISION",
    "ACOM_HANDOFF_MANIFEST",
    "STRUCTURED_RESULT",
    "ACOM_RESULT_INTAKE",
    "REVALIDATION_SCAFFOLD",
    "REVALIDATION_EXECUTION_RESULT",
    "SUPERVISOR_REVIEW_RESULT",
    "NON_SOLVER_EVIDENCE_LEDGER",
    "NON_SOLVER_EVIDENCE_SUMMARY",
    "SUPERVISOR_SUMMARY_ACK",
    "MARKDOWN_REPORT",
    "JSON_ARTIFACT",
    "UNKNOWN_READ_ONLY",
)


def classify_artifact(path: str | Path, *, frontmatter: dict[str, Any] | None = None, json_data: Any = None) -> str:
    target = Path(path)
    name = target.name.upper()
    normalized_path = str(target).replace("\\", "/").upper()
    frontmatter = frontmatter or {}
    doc_type = str(frontmatter.get("doc_type", "")).lower()

    if doc_type == "run_report":
        return "RUN_REPORT"
    if doc_type == "handoff":
        return "HANDOFF"
    if doc_type == "gate_decision":
        return "GATE_DECISION"

    if name == "HANDOFF_MANIFEST.JSON":
        return "ACOM_HANDOFF_MANIFEST"
    if name == "STRUCTURED_RESULT.JSON":
        return "STRUCTURED_RESULT"
    if name == "ACOM_RESULT_INTAKE.JSON":
        return "ACOM_RESULT_INTAKE"
    if name == "REVALIDATION_SCAFFOLD.JSON":
        return "REVALIDATION_SCAFFOLD"
    if name == "REVALIDATION_EXECUTION_RESULT.JSON":
        return "REVALIDATION_EXECUTION_RESULT"
    if name == "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.JSON":
        return "SUPERVISOR_REVIEW_RESULT"
    if "NON_SOLVER_EVIDENCE_LEDGER" in name:
        return "NON_SOLVER_EVIDENCE_LEDGER"
    if "NON_SOLVER_EVIDENCE_SUMMARY" in name:
        return "NON_SOLVER_EVIDENCE_SUMMARY"
    if "SUPERVISOR_NON_SOLVER_SUMMARY_ACK" in name or "NON_SOLVER_SUMMARY_ACK_LEDGER" in name:
        return "SUPERVISOR_SUMMARY_ACK"

    if isinstance(json_data, dict):
        keys = {str(key) for key in json_data}
        if {"handoff_id", "handoff_dir", "codex_task_path"} & keys and "CODEX_HANDOFF" in normalized_path:
            return "ACOM_HANDOFF_MANIFEST"
        if "revalidation_status" in keys or "revalidation_agent" in keys:
            return "REVALIDATION_EXECUTION_RESULT"
        if "supervisor_review_status" in keys:
            return "SUPERVISOR_REVIEW_RESULT"
        if "summary_status" in keys or "non_solver_evidence_summary_status" in keys:
            return "NON_SOLVER_EVIDENCE_SUMMARY"

    if target.suffix.lower() == ".md":
        return "MARKDOWN_REPORT"
    if target.suffix.lower() == ".json":
        return "JSON_ARTIFACT"
    return "UNKNOWN_READ_ONLY"
