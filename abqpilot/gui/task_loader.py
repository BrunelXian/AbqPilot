from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_task_summary(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    state = _read_json(task / "task_state.json")
    return {
        "status": "TASK_LOADED" if state else "TASK_LOAD_WARNING",
        "task_dir": str(task),
        "task_id": state.get("task_id") or task.name,
        "overall_status": state.get("status"),
        "current_step": state.get("current_step"),
        "updated_at": state.get("updated_at"),
        "errors": [] if state else [f"task_state.json could not be read under {task}"],
    }


def discover_recent_tasks(work_root: str | Path, limit: int = 10) -> list[dict[str, Any]]:
    root = Path(work_root)
    tasks_root = root / "tasks" if root.name != "tasks" else root
    if not tasks_root.exists():
        return []
    candidates = [path for path in tasks_root.iterdir() if path.is_dir()]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [load_task_summary(path) for path in candidates[:limit]]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
