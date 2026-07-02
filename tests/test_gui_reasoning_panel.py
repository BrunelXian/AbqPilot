import json

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui.app import AbqPilotGui


def test_gui_reasoning_panel_imports():
    assert AbqPilotGui is not None


def test_gui_real_reasoning_action_requires_confirmation(tmp_path):
    controller = GuiActionController(tmp_path)
    task_dir = _write_task(tmp_path)

    result = controller.run_real_llm_reasoner(task_dir, confirmed=False)

    assert result["verdict"] == "GUI_LLM_CONFIRMATION_REQUIRED"


def test_gui_mock_reasoning_action_does_not_call_network(monkeypatch, tmp_path):
    controller = GuiActionController(tmp_path)
    task_dir = _write_task(tmp_path)
    monkeypatch.setattr(
        "abqpilot.llm.provider.urllib.request.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network should not be called")),
    )

    result = controller.run_mock_reasoner(task_dir)

    assert result["command"] == "llm-reason"
    assert result["success"] is True


def test_gui_preview_llm_summary_returns_sanitized_summary(tmp_path):
    controller = GuiActionController(tmp_path)
    task_dir = _write_task(tmp_path)

    result = controller.preview_llm_input_summary(task_dir)

    assert result["verdict"] == "LLM_INPUT_SUMMARY_READY"
    assert result["details"]["sanitized_summary"]["task_id"] == "task"


def _write_task(tmp_path):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    task_dir.mkdir(parents=True)
    (task_dir / "task_state.json").write_text(
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
    (task_dir / "artifacts.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    (task_dir / "pipeline_trace.json").write_text(json.dumps({"events": []}), encoding="utf-8")
    return task_dir
