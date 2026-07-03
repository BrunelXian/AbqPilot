from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def read_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def write_json(path: str | Path, payload: dict[str, Any]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(target)


def write_text(path: str | Path, text: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return str(target)


def result(command: str, verdict: str, success: bool, run_dir: str | Path, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": command,
        "verdict": verdict,
        "success": bool(success),
        "output_paths": {"artifact_dir": str(Path(run_dir))},
        "details": details,
        "errors": details.get("errors", []),
        "warnings": details.get("warnings", []),
    }


def tail_text(path: str | Path, limit: int = 4000) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-limit:] if len(text) > limit else text
