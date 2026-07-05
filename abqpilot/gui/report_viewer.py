from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.artifact_preview import build_artifact_preview
from abqpilot.gui.status_badges import status_badge


READ_ONLY_NOTICE = "Read-only preview. This viewer does not modify artifacts."
CLAIM_BOUNDARY_NOTICE = (
    "Final evidence remains locked. Codex output is structured input, not final evidence. "
    "Non-solver summary acknowledgement is non-final."
)
SAFETY_BOUNDARY_NOTICE = (
    "Solver / ODB / metrics remain disabled. Unsafe approval claims are flagged, not fixed."
)


def build_report_viewer_card(path: str | Path | None) -> dict[str, Any]:
    preview = build_artifact_preview(path)
    status = str(preview.get("parse_status"))
    card = {
        "title": preview.get("filename") or "No artifact selected",
        "artifact_type": preview.get("artifact_type", "UNKNOWN_READ_ONLY"),
        "status_badge": status_badge(status),
        "file_path": preview.get("path"),
        "key_metadata": _metadata(preview),
        "important_sections": _important_sections(preview),
        "warnings": preview.get("warning_items", []),
        "blocked_items": preview.get("blocked_items", []),
        "unsafe_claims": preview.get("unsafe_claims", []),
        "read_only_notice": READ_ONLY_NOTICE,
        "safety_boundary_notice": SAFETY_BOUNDARY_NOTICE,
        "claim_boundary_notice": CLAIM_BOUNDARY_NOTICE,
        "preview": preview,
        "read_only": True,
        "action_allowed": False,
    }
    return card


def render_report_viewer_text(card: dict[str, Any]) -> str:
    metadata = card.get("key_metadata", {})
    sections = card.get("important_sections", {})
    lines = [
        "Read-only preview",
        str(card.get("title")),
        "",
        "Artifact Type",
        str(card.get("artifact_type")),
        "",
        "Status",
        str(card.get("status_badge")),
        "",
        "Path",
        str(card.get("file_path")),
        "",
        "Metadata",
    ]
    for key, value in metadata.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "Claim Boundary",
            str(card.get("claim_boundary_notice")),
            "",
            "Safety Boundary",
            str(card.get("safety_boundary_notice")),
            "",
            "Important Sections",
        ]
    )
    if sections:
        for name, text in sections.items():
            lines.append(f"\n## {name}")
            lines.append(str(text)[:1600])
    else:
        lines.append("No key Markdown sections detected.")
    warnings = card.get("warnings", [])
    blocked = card.get("blocked_items", [])
    unsafe = card.get("unsafe_claims", [])
    if warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"- {item}" for item in warnings[:20])
    if blocked:
        lines.extend(["", "Blocked / Parse Items"])
        lines.extend(f"- {item}" for item in blocked[:20])
    if unsafe:
        lines.extend(["", "Unsafe Approval Claims"])
        lines.extend(f"- {item.get('key')}={item.get('value')} at {item.get('path')}" for item in unsafe[:20])
    lines.extend(
        [
            "",
            str(card.get("read_only_notice")),
            "This viewer does not modify artifacts.",
            "Unsafe approval claims are flagged, not fixed.",
        ]
    )
    return "\n".join(lines)


def _metadata(preview: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "file_type": preview.get("file_type"),
        "exists": preview.get("exists"),
        "parse_status": preview.get("parse_status"),
        "read_only": preview.get("read_only"),
    }
    if preview.get("file_type") == "json":
        metadata["top_level_keys"] = preview.get("top_level_keys", [])
        metadata["status_fields"] = preview.get("status_fields", {})
        metadata["decision_fields"] = preview.get("decision_fields", {})
    if preview.get("file_type") == "markdown":
        metadata["heading_count"] = len(preview.get("headings", []))
        metadata["frontmatter_keys"] = sorted(preview.get("frontmatter", {}).keys())
    return metadata


def _important_sections(preview: dict[str, Any]) -> dict[str, str]:
    if preview.get("file_type") == "markdown":
        return dict(preview.get("key_sections", {}))
    if preview.get("file_type") == "json":
        sections: dict[str, str] = {}
        for key in ("status_fields", "decision_fields", "safety_fields"):
            value = preview.get(key)
            if value:
                sections[key] = str(value)
        return sections
    return {}
