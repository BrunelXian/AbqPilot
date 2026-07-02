import json
from types import SimpleNamespace

from abqpilot.llm.config import LlmConfig
from abqpilot.llm.input_builder import build_sanitized_task_summary
from abqpilot.llm.mock_reasoner import MockReasoner
from abqpilot.llm.provider import OpenAICompatibleProvider
from abqpilot.llm.schema import validate_reasoning_response


def test_mock_reasoner_returns_valid_schema():
    result = MockReasoner().reason({"task_id": "task", "failed_steps": []})

    assert result["verdict"] == "OK"
    assert result["validation"]["valid"] is True
    assert result["human_review_required"] is True


def test_schema_validator_rejects_unsafe_payload():
    validation = validate_reasoning_response(
        {
            "schema_version": "0.1",
            "provider": "mock",
            "model": "mock",
            "verdict": "ACTION_RECOMMENDED",
            "observation": "bad",
            "diagnosis": "bad",
            "recommended_next_action": "submit solver now",
            "allowed_actions": ["submit solver"],
            "blocked_actions": [],
            "risk_flags": [],
            "human_review_required": True,
            "confidence": 0.5,
        }
    )

    assert validation["valid"] is False


def test_provider_returns_disabled_without_api_call(monkeypatch):
    called = []
    monkeypatch.setattr("abqpilot.llm.provider.urllib.request.urlopen", lambda *_args, **_kwargs: called.append("called"))
    provider = OpenAICompatibleProvider(LlmConfig(enabled=False, api_key="test-secret", chat_url="https://example.invalid"))

    result = provider.reason({"task_id": "task"})

    assert result["verdict"] == "LLM_DISABLED"
    assert called == []


def test_provider_probe_uses_monkeypatched_urlopen(monkeypatch):
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr("abqpilot.llm.provider.urllib.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleProvider(
        LlmConfig(
            enabled=True,
            provider="chatanywhere",
            model="deepseek-chat",
            api_key="test-secret",
            chat_url="https://example.invalid/v1/chat/completions",
        )
    )

    result = provider.probe()

    assert result["verdict"] == "PASS"
    assert calls


def test_sanitized_task_summary_excludes_paths_and_binary_content(tmp_path):
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "task_state.json").write_text(
        json.dumps({"task_id": "task", "status": "WAITING", "completed_steps": [], "failed_steps": [], "skipped_steps": []}),
        encoding="utf-8",
    )
    (task_dir / "artifacts.json").write_text(
        json.dumps({"artifacts": [{"name": "generated_power_x2", "path": "D:/secret/model.inp"}]}),
        encoding="utf-8",
    )

    summary = build_sanitized_task_summary(task_dir)

    assert "artifact_refs" in summary
    assert "D:/secret/model.inp" not in json.dumps(summary)
    assert summary["safety_boundaries"]["includes_full_inp"] is False
