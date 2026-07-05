from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.trace_viewer import build_trace_viewer


def select_timeline_step(task_dir: str | Path | None, step_id: str) -> dict[str, Any]:
    viewer = build_trace_viewer(task_dir)
    selected = next((step for step in viewer.get("timeline_steps", []) if step.get("step_id") == step_id), None)
    if selected is None:
        selected = {
            "step_id": step_id,
            "display_name": step_id,
            "status": "TIMELINE_STEP_MISSING",
            "related_run_files": [],
            "related_handoff_files": [],
            "related_gate_files": [],
            "related_json_files": [],
            "related_markdown_reports": [],
            "missing_expected_files": [step_id],
            "selectable": False,
            "read_only": True,
            "action_allowed": False,
        }
    return {
        "viewer_state": viewer.get("viewer_state"),
        "selected_step": selected,
        "read_only": True,
        "timeline_selection_executes_actions": False,
        "action_allowed": False,
        "claim_boundary": "Timeline selection displays evidence records only; it does not approve evidence.",
        "safety_boundary": "Timeline selection does not execute actions. Final evidence remains locked.",
    }
