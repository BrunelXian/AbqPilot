from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.pipeline_protocol.frontmatter import parse_frontmatter_text


TEXT_SUFFIXES = {".md", ".txt", ".json", ".log", ".sta", ".msg", ".dat", ".csv"}


def build_read_only_document_view(path: str | Path | None, max_lines: int = 80) -> dict[str, Any]:
    if path is None:
        return _empty_view(None, "missing path")
    target = Path(path)
    if not target.exists() or not target.is_file():
        return _empty_view(str(target), "missing file")
    if target.suffix.lower() not in TEXT_SUFFIXES:
        return {
            "path": str(target),
            "exists": True,
            "read_only": True,
            "editable": False,
            "frontmatter": {},
            "body": "",
            "first_lines": [],
            "full_text": "",
            "warnings": ["binary or unsupported text preview type"],
        }
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return _empty_view(str(target), str(exc))
    frontmatter: dict[str, Any] = {}
    body = text
    if target.suffix.lower() == ".md":
        frontmatter, body = parse_frontmatter_text(text)
    elif target.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
            frontmatter = payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            frontmatter = {}
    lines = body.splitlines()
    return {
        "path": str(target),
        "exists": True,
        "read_only": True,
        "editable": False,
        "frontmatter": frontmatter,
        "body": body,
        "first_lines": lines[:max_lines],
        "full_text": text,
        "warnings": [],
    }


def _empty_view(path: str | None, warning: str) -> dict[str, Any]:
    return {
        "path": path,
        "exists": False,
        "read_only": True,
        "editable": False,
        "frontmatter": {},
        "body": "",
        "first_lines": [],
        "full_text": "",
        "warnings": [warning],
    }
