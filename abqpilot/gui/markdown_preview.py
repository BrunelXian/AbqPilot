from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.artifact_type_classifier import classify_artifact
from abqpilot.gui.preview_safety import collect_safety_fields, find_unsafe_claims
from abqpilot.gui.section_extractor import extract_headings, extract_key_sections
from abqpilot.pipeline_protocol.frontmatter import parse_frontmatter_text


def build_markdown_preview(path: str | Path, *, max_lines: int = 80) -> dict[str, Any]:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return _missing(target)
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {
            "path": str(target),
            "filename": target.name,
            "file_type": "markdown",
            "exists": True,
            "parse_status": "ARTIFACT_PREVIEW_PARSE_ERROR",
            "parse_error": str(exc),
            "read_only": True,
            "unsafe_claims": [],
        }

    frontmatter, body = parse_frontmatter_text(text)
    headings = extract_headings(body)
    key_sections = extract_key_sections(body)
    unsafe_claims = find_unsafe_claims(frontmatter, path=str(target))
    warning_items = _lines_with_terms(body, ("warning", "requires human review", "review required"))
    blocked_items = _lines_with_terms(body, ("blocked", "fail", "unsafe"))
    parse_status = "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM" if unsafe_claims else "ARTIFACT_PREVIEW_READY"
    return {
        "path": str(target),
        "filename": target.name,
        "file_type": "markdown",
        "artifact_type": classify_artifact(target, frontmatter=frontmatter),
        "exists": True,
        "parse_status": parse_status,
        "frontmatter": frontmatter,
        "markdown_body": body,
        "headings": headings,
        "key_sections": key_sections,
        "first_lines": body.splitlines()[:max_lines],
        "safety_fields": collect_safety_fields(frontmatter),
        "claim_boundary_text": _section_text(key_sections, "Claim Boundary"),
        "safety_boundary_text": _section_text(key_sections, "Safety Boundary") or _section_text(key_sections, "Guardrails"),
        "warning_items": warning_items,
        "blocked_items": blocked_items,
        "unsafe_claims": unsafe_claims,
        "read_only": True,
        "editable": False,
        "preview_notice": "Read-only preview. This viewer does not modify artifacts.",
    }


def _missing(target: Path) -> dict[str, Any]:
    return {
        "path": str(target),
        "filename": target.name,
        "file_type": "markdown",
        "exists": False,
        "parse_status": "ARTIFACT_PREVIEW_MISSING_FILE",
        "frontmatter": {},
        "markdown_body": "",
        "headings": [],
        "key_sections": {},
        "first_lines": [],
        "safety_fields": {},
        "claim_boundary_text": "",
        "safety_boundary_text": "",
        "warning_items": [],
        "blocked_items": [],
        "unsafe_claims": [],
        "read_only": True,
        "editable": False,
    }


def _section_text(sections: dict[str, str], key: str) -> str:
    return sections.get(key, "")


def _lines_with_terms(body: str, terms: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    lower_terms = tuple(term.lower() for term in terms)
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and any(term in stripped.lower() for term in lower_terms):
            result.append(stripped)
    return result[:20]
