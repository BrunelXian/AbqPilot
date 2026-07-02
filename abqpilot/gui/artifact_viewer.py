from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PREVIEW_MAX_BYTES = 1024 * 1024
TEXT_SUFFIXES = {".md", ".txt", ".log", ".csv"}


def preview_artifact(path: str | Path | None, max_bytes: int = PREVIEW_MAX_BYTES) -> dict[str, Any]:
    if not path:
        return _result("NO_ARTIFACT_SELECTED", None, "No artifact selected.", previewable=False)
    target = Path(path)
    if not target.exists():
        return _result("ARTIFACT_MISSING", target, f"Missing artifact:\n{target}", previewable=False)
    if target.is_dir():
        return _result("ARTIFACT_IS_DIRECTORY", target, f"Folder:\n{target}", previewable=False)
    suffix = target.suffix.lower()
    if suffix not in {".json"} | TEXT_SUFFIXES:
        return _result("ARTIFACT_PATH_ONLY", target, f"Path only:\n{target}", previewable=False)
    size = target.stat().st_size
    truncated = size > max_bytes
    payload = target.read_bytes()[:max_bytes]
    text = payload.decode("utf-8", errors="replace")
    if suffix == ".json":
        try:
            text = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    if truncated:
        text += f"\n\n[Preview truncated at {max_bytes} bytes from {size} bytes.]"
    return _result("ARTIFACT_PREVIEW_READY", target, text, previewable=True, truncated=truncated, size_bytes=size)


def _result(
    status: str,
    path: Path | None,
    preview: str,
    previewable: bool,
    truncated: bool = False,
    size_bytes: int | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "path": str(path) if path is not None else None,
        "preview": preview,
        "previewable": previewable,
        "truncated": truncated,
        "size_bytes": size_bytes,
    }
