import json
from pathlib import Path

from abqpilot import cli
from abqpilot.reporting.project_status import export_project_status
from abqpilot.ui_state.view_model import build_task_view_model


SECRET = "test-secret-value"


def test_llm_reason_mock_works_without_env(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    task_dir = _write_task(tmp_path)

    result = cli.command_llm_reason(task_dir=task_dir, provider="mock")

    assert result["verdict"] == "OK"
    assert result["details"]["provider_config"]["api_key"] == "<not-configured>"


def test_probe_llm_requires_confirm(monkeypatch, tmp_path):
    _write_env(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli.command_probe_llm(provider="chatanywhere", model="deepseek-chat")

    assert result["verdict"] == "LLM_PROBE_CONFIRMATION_REQUIRED"
    assert SECRET not in json.dumps(result)


def test_llm_reason_real_provider_requires_confirm(monkeypatch, tmp_path):
    _write_env(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    task_dir = _write_task(tmp_path)

    result = cli.command_llm_reason(task_dir=task_dir, provider="chatanywhere", model="deepseek-chat")

    assert result["verdict"] == "LLM_TASK_SUMMARY_CONFIRMATION_REQUIRED"
    assert SECRET not in json.dumps(result)


def test_llm_disabled_result_when_confirmed_but_disabled(monkeypatch, tmp_path):
    _write_env(tmp_path, enabled="false")
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    task_dir = _write_task(tmp_path)

    result = cli.command_llm_reason(
        task_dir=task_dir,
        provider="chatanywhere",
        model="deepseek-chat",
        confirm_send_task_summary=True,
    )

    assert result["verdict"] == "LLM_DISABLED"
    assert SECRET not in json.dumps(result)


def test_llm_result_json_does_not_contain_api_key(monkeypatch, tmp_path):
    _write_env(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    result_json = tmp_path / "llm.json"

    cli.command_probe_llm(provider="chatanywhere", model="deepseek-chat", result_json=result_json)

    assert SECRET not in result_json.read_text(encoding="utf-8")


def test_project_status_and_gui_view_model_do_not_include_api_key(tmp_path):
    _write_env(tmp_path)
    task_dir = _write_task(tmp_path)

    status = export_project_status(root=tmp_path)
    view_model = build_task_view_model(task_dir)

    assert SECRET not in Path(status["output_paths"]["project_status_json"]).read_text(encoding="utf-8")
    assert SECRET not in Path(status["output_paths"]["project_status_md"]).read_text(encoding="utf-8")
    assert SECRET not in json.dumps(view_model)


def test_cli_parser_accepts_llm_commands():
    parser = cli.build_parser()

    reason = parser.parse_args(["llm-reason", "--task-dir", "task", "--provider", "mock"])
    probe = parser.parse_args(["probe-llm", "--provider", "chatanywhere"])

    assert reason.command == "llm-reason"
    assert probe.command == "probe-llm"


def _write_env(tmp_path, enabled="true"):
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                f"ABQPILOT_LLM_ENABLED={enabled}",
                "ABQPILOT_LLM_PROVIDER=chatanywhere",
                "ABQPILOT_LLM_MODEL=deepseek-chat",
                f"ABQPILOT_LLM_API_KEY={SECRET}",
                "ABQPILOT_LLM_CHAT_URL=https://example.invalid/v1/chat/completions",
                "ABQPILOT_LLM_TIMEOUT_SECONDS=1",
            ]
        ),
        encoding="utf-8",
    )


def _write_task(tmp_path):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task_state.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "status": "WAITING_FOR_ABQJOBPILOT",
                "current_step": "07_abqjobpilot_status_poll",
                "completed_steps": ["07_abqjobpilot_status_poll"],
                "failed_steps": [],
                "skipped_steps": [],
                "steps": {"07_abqjobpilot_status_poll": {"status": "COMPLETED", "verdict": "JOB_QUEUED"}},
                "safety_flags": {"allow_solver_submit": False, "allow_llm": False, "allow_codex_runtime": False},
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "artifacts.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    (task_dir / "pipeline_trace.json").write_text(json.dumps({"events": []}), encoding="utf-8")
    return task_dir
