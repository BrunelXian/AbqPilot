import json

from abqpilot.llm.input_builder import build_sanitized_task_summary


def test_input_summary_excludes_sensitive_content_and_paths(tmp_path):
    task = tmp_path / "task"
    task.mkdir()
    (task / "task_state.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "status": "WAITING_FOR_ABQJOBPILOT",
                "current_step": "07_abqjobpilot_status_poll",
                "steps": {"07_abqjobpilot_status_poll": {"status": "COMPLETED", "verdict": "JOB_QUEUED"}},
                "completed_steps": ["07_abqjobpilot_status_poll"],
                "failed_steps": [],
                "skipped_steps": [],
            }
        ),
        encoding="utf-8",
    )
    (task / "artifacts.json").write_text(
        json.dumps(
            {
                "artifacts": [
                    {"name": "candidate_inp", "kind": "file", "path": "D:/private/full/model.inp"},
                    {"name": "solver_odb", "kind": "file", "path": "D:/private/full/model.odb"},
                    {"name": "cae", "kind": "file", "path": "D:/private/full/model.cae"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (task / "pipeline_trace.json").write_text(json.dumps({"events": []}), encoding="utf-8")

    summary = build_sanitized_task_summary(task)
    text = json.dumps(summary, ensure_ascii=False)

    assert "D:/private/full" not in text
    assert "full/model.inp" not in text
    assert "odb content" not in text.lower()
    assert "api_key" not in text.lower()
    assert summary["safety_boundaries"]["direct_odb_open_allowed"] is False


def test_input_summary_respects_max_char_limit(tmp_path):
    task = tmp_path / "task"
    task.mkdir()
    (task / "task_state.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "status": "WAITING",
                "steps": {f"{idx:02d}_step": {"status": "COMPLETED", "verdict": "OK"} for idx in range(100)},
                "completed_steps": [],
                "failed_steps": [],
                "skipped_steps": [],
            }
        ),
        encoding="utf-8",
    )
    (task / "artifacts.json").write_text(
        json.dumps({"artifacts": [{"name": f"artifact_{idx}", "path": f"D:/x/{idx}.json"} for idx in range(200)]}),
        encoding="utf-8",
    )
    (task / "pipeline_trace.json").write_text(json.dumps({"events": []}), encoding="utf-8")

    summary = build_sanitized_task_summary(task, max_chars=900)

    assert summary["input_truncated"] is True
    assert len(json.dumps(summary, ensure_ascii=False, sort_keys=True)) < 2500
