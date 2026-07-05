from __future__ import annotations

from pathlib import Path

from abqpilot.gui.timeline_interaction import select_timeline_step
from abqpilot.gui.workflow_timeline import TIMELINE_STAGES


SMOKE_TASK = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")


def test_timeline_interaction_module_imports():
    assert callable(select_timeline_step)


def test_all_timeline_steps_are_selectable_read_only():
    for step_id, _label in TIMELINE_STAGES:
        result = select_timeline_step(SMOKE_TASK, step_id)
        step = result["selected_step"]
        assert step["selectable"] is True
        assert step["read_only"] is True
        assert step["action_allowed"] is False
        assert result["timeline_selection_executes_actions"] is False


def test_timeline_selection_resolves_expected_stage_artifacts():
    assert select_timeline_step(SMOKE_TASK, "acom_handoff")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "acom_result_intake")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "revalidation_scaffold")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "non_solver_revalidation")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "supervisor_review")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "non_solver_ledger")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "evidence_summary")["selected_step"]["related_json_files"]
    assert select_timeline_step(SMOKE_TASK, "supervisor_ack")["selected_step"]["related_json_files"]
