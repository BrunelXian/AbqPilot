from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.action_panels import build_action_panels, build_controlled_solver_gate_panel, build_high_risk_gate_panel
from abqpilot.gui.recommendation_cards import build_next_step_recommendation_card
from abqpilot.gui.status_cards import (
    build_disabled_actions_card,
    build_next_safe_action_card,
    build_project_header_card,
    build_task_workspace_card,
    build_trace_summary_card,
)
from abqpilot.gui.workflow_presenter import build_gui_workflow_presenter
from abqpilot.gui.workflow_timeline import build_workflow_timeline, render_timeline_text


def build_layout_sections(task_dir: str | Path | None, project_root: str | Path | None = None) -> dict[str, Any]:
    presenter = build_gui_workflow_presenter(task_dir, project_root)
    timeline = build_workflow_timeline(presenter["workflow_state"])
    return {
        "top_project_header": build_project_header_card(presenter),
        "task_sidebar": build_task_workspace_card(presenter),
        "workflow_timeline": timeline,
        "workflow_timeline_text": render_timeline_text(timeline),
        "next_safe_action_card": build_next_safe_action_card(presenter),
        "guided_next_step_recommendation": build_next_step_recommendation_card(task_dir),
        "disabled_high_risk_actions_card": build_disabled_actions_card(presenter),
        "trace_record_summary": build_trace_summary_card(presenter),
        "action_panels": build_action_panels(),
        "high_risk_gate_panel": build_high_risk_gate_panel(),
        "controlled_solver_gate_panel": build_controlled_solver_gate_panel(str(task_dir) if task_dir else None),
        "copy": [
            "Non-final / non-solver workflow",
            "Final evidence remains locked",
            "Solver, ODB, metrics, and model mutation are disabled",
            "Codex executes externally; GUI does not call Codex CLI",
            "Accepted ACOM result means accepted for AbqPilot revalidation, not evidence",
            "Supervisor acknowledgement does not freeze final verdict",
            "High-risk action locked",
            "Preview only; not an approval",
            "Human gate required in a future explicit stage",
            "Controlled Solver Run is locked",
            "Preview only; not a solver approval",
            "No Abaqus solver command is executed",
            "Draft only; not an active execution handoff",
            "No solver request file is created",
            "Future ExecutionAgent stage is required",
            "Draft schema only; not an active solver request",
            "No solver_request.json is created",
            "Preflight only; no solver execution",
            "No output directory for execution is created",
            "Dry-run request artifact only; not an active solver_request.json",
            "No queue entry is created",
            "Controlled solver demo smoke run is limited to the Stage 5.3A smoke task",
            "ODB not opened",
            "Metrics not extracted",
        ],
    }
