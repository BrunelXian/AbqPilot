import json

from abqpilot.llm.patch_context_builder import build_patch_context


def test_patch_context_excludes_file_content_paths_and_secret(tmp_path):
    task = _task(tmp_path)
    (task / "artifacts.json").write_text(
        json.dumps(
            {
                "artifacts": [
                    {"name": "candidate_inp", "kind": "file", "path": "D:/secret/model.inp"},
                    {"name": "solver_odb", "kind": "file", "path": "D:/secret/model.odb"},
                ]
            }
        ),
        encoding="utf-8",
    )

    context = build_patch_context(task)
    text = json.dumps(context, ensure_ascii=False)

    assert "D:/secret" not in text
    assert "full inp" not in text.lower()
    assert "odb content" not in text.lower()
    assert "api_key" not in text.lower()
    assert context["safety_boundaries"]["llm_can_mutate_inp"] is False


def test_patch_context_includes_deterministic_repair_plan_summary(tmp_path):
    task = _task(tmp_path)
    analysis = task / "analysis"
    analysis.mkdir()
    (analysis / "repair_plan.json").write_text(
        json.dumps(
            {
                "evaluation_verdict": "PASS_THERMAL_RESPONSE_CONFIRMED",
                "repair_required": False,
                "recommended_next_action": "Export Run Report",
                "allowed_patch_types": ["heat_flux_magnitude_adjustment"],
                "forbidden_patch_types": ["material_change"],
            }
        ),
        encoding="utf-8",
    )

    context = build_patch_context(task)

    assert context["deterministic_repair_plan"]["repair_required"] is False
    assert "heat_flux_magnitude_adjustment" in context["deterministic_repair_plan"]["allowed_patch_types"]


def _task(tmp_path):
    task = tmp_path / "task"
    task.mkdir()
    (task / "task_state.json").write_text(
        json.dumps({"task_id": "task", "status": "PASS", "failed_steps": []}),
        encoding="utf-8",
    )
    (task / "artifacts.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    return task
