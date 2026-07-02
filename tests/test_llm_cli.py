import json

from abqpilot import cli


SECRET = "sk-cli-test-secret-not-real"


def test_dry_run_input_summary_does_not_call_provider(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task_dir = _write_task(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "abqpilot.llm.provider.urllib.request.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network should not be called")),
    )

    result = cli.command_llm_reason(task_dir=task_dir, provider="chatanywhere", dry_run_input_summary=True)

    assert result["verdict"] == "LLM_INPUT_SUMMARY_READY"
    assert result["details"]["sent_task_summary"] is False


def test_show_sanitized_summary_does_not_include_secret(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task_dir = _write_task(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli.command_llm_reason(
        task_dir=task_dir,
        provider="mock",
        show_sanitized_summary=True,
    )

    assert SECRET not in json.dumps(result)
    assert result["details"]["sanitized_summary"]["safety_boundaries"]["includes_secret"] is False


def test_chatanywhere_reason_requires_confirm(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task_dir = _write_task(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli.command_llm_reason(task_dir=task_dir, provider="chatanywhere", model="deepseek-chat")

    assert result["verdict"] == "LLM_TASK_SUMMARY_CONFIRMATION_REQUIRED"
    assert result["details"]["sent_task_summary"] is False


def test_confirmed_chatanywhere_reason_uses_monkeypatched_provider(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task_dir = _write_task(tmp_path)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    calls = []

    def fake_reason(self, summary):
        calls.append(summary)
        return {
            "schema_version": "0.1",
            "provider": "chatanywhere",
            "model": "deepseek-chat",
            "verdict": "WAITING",
            "observation": "Queued.",
            "diagnosis": "Wait for outputs.",
            "recommended_next_action": "Poll JobPilot Status",
            "allowed_actions": ["poll_jobpilot_status"],
            "blocked_actions": ["submit_solver"],
            "risk_flags": [],
            "human_review_required": True,
            "confidence": 0.9,
            "validation": {"valid": True, "status": "PASS", "errors": [], "forbidden_recommendations": []},
        }

    monkeypatch.setattr("abqpilot.llm.provider.OpenAICompatibleProvider.reason", fake_reason)

    result = cli.command_llm_reason(
        task_dir=task_dir,
        provider="chatanywhere",
        model="deepseek-chat",
        confirm_send_task_summary=True,
    )

    assert len(calls) == 1
    assert result["verdict"] == "WAITING"
    assert result["details"]["sent_task_summary"] is True
    assert "llm_reasoning_result" in result["output_paths"]
    assert SECRET not in json.dumps(result)


def test_cli_parser_accepts_stage35b_flags():
    parser = cli.build_parser()

    args = parser.parse_args(["llm-reason", "--dry-run-input-summary", "--show-sanitized-summary"])

    assert args.command == "llm-reason"
    assert args.dry_run_input_summary is True
    assert args.show_sanitized_summary is True


def _write_env(tmp_path):
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "ABQPILOT_LLM_ENABLED=true",
                "ABQPILOT_LLM_PROVIDER=chatanywhere",
                "ABQPILOT_LLM_MODEL=deepseek-chat",
                f"ABQPILOT_LLM_API_KEY={SECRET}",
                "ABQPILOT_LLM_CHAT_URL=https://example.invalid/v1/chat/completions",
            ]
        ),
        encoding="utf-8",
    )


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
