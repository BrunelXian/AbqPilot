from pathlib import Path

from abqpilot.gui.next_step_recommender import build_next_step_recommendation


def test_next_step_recommender_imports() -> None:
    assert callable(build_next_step_recommendation)


def test_no_task_selected_maps_to_no_task_recommendation() -> None:
    result = build_next_step_recommendation(None)
    assert result["recommendation_status"] == "NEXT_STEP_NO_TASK_SELECTED"
    assert result["auto_execute_allowed"] is False
    assert result["codex_execution_allowed"] is False


def test_existing_stage5_0i_task_maps_to_acknowledged_non_solver_state() -> None:
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    result = build_next_step_recommendation(task)
    assert result["recommendation_status"] == "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED"
    assert result["final_evidence_approved"] is False
    assert result["final_verdict_frozen"] is False
    assert result["solver_approved"] is False
    assert result["odb_approved"] is False
    assert result["metrics_approved"] is False


def test_recommender_reads_high_risk_downstream_agent_from_scaffold(tmp_path: Path) -> None:
    task = tmp_path / "task"
    scaffold_dir = task / "revalidation" / "GuardAgent_001"
    scaffold_dir.mkdir(parents=True)
    (task / "TRACE_INDEX.md").write_text("---\ndoc_type: trace_index\ntask_id: task\nstatus: ready\n---\n", encoding="utf-8")
    (scaffold_dir / "REVALIDATION_SCAFFOLD.json").write_text('{"downstream_agent":"GuardAgent"}', encoding="utf-8")
    result = build_next_step_recommendation(task)
    assert result["recommendation_status"] == "NEXT_STEP_REVIEW_REQUIRED"
    assert result["recommended_action_id"] != "execute_non_solver_revalidation"
    assert result["blocked_reasons"]
