from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.workflow_state import inspect_gui_workflow_state


def build_task_workspace_view(task_dir: str | Path | None) -> dict[str, Any]:
    state = inspect_gui_workflow_state(task_dir)
    return {
        "selected_task_dir": state["task_dir"],
        "task_id": state["task_id"],
        "task_exists": state["task_exists"],
        "task_scaffold_status": "present" if state["trace_index_exists"] else "missing_trace_index",
        "run_count": state["run_records"]["count"],
        "handoff_count": state["handoff_records"]["count"],
        "gate_count": state["gate_records"]["count"],
        "latest_run": state["run_records"]["latest_path"],
        "latest_gate": state["gate_records"]["latest_path"],
        "latest_status": state["latest_status"],
        "final_evidence_locked": state["final_evidence_locked"],
    }
