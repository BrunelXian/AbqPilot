from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def make_task_result(
    command: str,
    verdict: str,
    success: bool,
    output_paths: dict[str, str] | None = None,
    safety_flags: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "command": command,
        "verdict": verdict,
        "success": bool(success),
        "output_paths": output_paths or {},
        "safety_flags": safety_flags or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "details": details or {},
    }


def write_result_json(result: dict[str, Any], path: str | Path | None) -> None:
    if path is None:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def write_json(path: str | Path, payload: dict[str, Any]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(target)
