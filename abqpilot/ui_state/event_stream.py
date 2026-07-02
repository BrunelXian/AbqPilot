from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.ui_state.module_registry import module_id_for_step


def build_event_stream(task_dir: str | Path) -> list[dict[str, Any]]:
    task = Path(task_dir)
    events: list[dict[str, Any]] = []
    trace_path = task / "pipeline_trace.json"
    if trace_path.exists():
        trace = _read_json(trace_path).get("events", [])
        for item in trace:
            events.append(
                {
                    "timestamp": item.get("timestamp"),
                    "level": _level_for_event(item.get("event"), item.get("verdict")),
                    "module_id": module_id_for_step(item.get("step")) or "pipeline",
                    "title": item.get("event") or "PIPELINE_EVENT",
                    "message": item.get("reason") or item.get("verdict") or "",
                    "artifact_path": item.get("result_path"),
                    "status": item.get("verdict"),
                }
            )
    for result_path in sorted((task / "steps").glob("*/step_result.json")) if (task / "steps").exists() else []:
        result = _read_json(result_path)
        events.append(
            {
                "timestamp": None,
                "level": "SUCCESS" if result.get("success") else "ERROR",
                "module_id": module_id_for_step(result.get("command")) or "pipeline",
                "title": result.get("command"),
                "message": result.get("verdict"),
                "artifact_path": str(result_path),
                "status": result.get("verdict"),
            }
        )
    return sorted(events, key=lambda item: item.get("timestamp") or "")


def _level_for_event(event: str | None, verdict: str | None) -> str:
    if event in {"STEP_FAILED", "PIPELINE_FAILED"}:
        return "ERROR"
    if event in {"STEP_COMPLETED", "PIPELINE_STOPPED"} and verdict and "PASS" in str(verdict):
        return "SUCCESS"
    if event == "STEP_SKIPPED":
        return "WARNING"
    return "INFO"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
