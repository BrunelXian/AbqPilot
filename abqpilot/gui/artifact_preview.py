from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from abqpilot.gui.artifact_type_classifier import classify_artifact
from abqpilot.gui.json_preview import build_json_preview
from abqpilot.gui.markdown_preview import build_markdown_preview


class ArtifactPreviewState(StrEnum):
    READY = "ARTIFACT_PREVIEW_READY"
    READY_WITH_WARNINGS = "ARTIFACT_PREVIEW_READY_WITH_WARNINGS"
    MISSING_FILE = "ARTIFACT_PREVIEW_MISSING_FILE"
    UNSUPPORTED_TYPE = "ARTIFACT_PREVIEW_UNSUPPORTED_TYPE"
    PARSE_ERROR = "ARTIFACT_PREVIEW_PARSE_ERROR"
    BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM = "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
    REVIEW_REQUIRED = "ARTIFACT_PREVIEW_REVIEW_REQUIRED"


SUPPORTED_SUFFIXES = {".md", ".json"}


def build_artifact_preview(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return _missing(None)
    target = Path(path)
    if not target.exists() or not target.is_file():
        return _missing(target)
    suffix = target.suffix.lower()
    if suffix == ".md":
        preview = build_markdown_preview(target)
    elif suffix == ".json":
        preview = build_json_preview(target)
    else:
        preview = _unsupported(target)
    preview.setdefault("schema_version", "0.1")
    preview.setdefault("stage", "Stage 5.1D")
    preview.setdefault("read_only", True)
    preview.setdefault("editable", False)
    preview.setdefault("mutation_allowed", False)
    preview.setdefault("external_open_allowed", False)
    preview.setdefault("execution_allowed", False)
    preview.setdefault("final_evidence_approved", False)
    preview.setdefault("final_verdict_frozen", False)
    preview.setdefault("solver_approved", False)
    preview.setdefault("odb_metrics_approved", False)
    return preview


def _missing(target: Path | None) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.1D",
        "path": str(target) if target else None,
        "filename": target.name if target else None,
        "file_type": "unknown",
        "artifact_type": "UNKNOWN_READ_ONLY",
        "exists": False,
        "parse_status": ArtifactPreviewState.MISSING_FILE.value,
        "read_only": True,
        "editable": False,
        "mutation_allowed": False,
        "external_open_allowed": False,
        "execution_allowed": False,
        "unsafe_claims": [],
        "warning_items": [],
        "blocked_items": ["missing file"],
    }


def _unsupported(target: Path) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.1D",
        "path": str(target),
        "filename": target.name,
        "file_type": target.suffix.lower().lstrip(".") or "unknown",
        "artifact_type": classify_artifact(target),
        "exists": True,
        "parse_status": ArtifactPreviewState.UNSUPPORTED_TYPE.value,
        "unsupported_reason": "UNSUPPORTED_READ_ONLY_PREVIEW",
        "read_only": True,
        "editable": False,
        "mutation_allowed": False,
        "external_open_allowed": False,
        "execution_allowed": False,
        "unsafe_claims": [],
        "warning_items": [],
        "blocked_items": [],
        "frontmatter": {},
        "json_data": None,
    }
