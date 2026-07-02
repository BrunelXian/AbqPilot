import json

from abqpilot.llm.artifacts import write_reasoning_artifacts
from abqpilot.llm.config import LlmConfig
from abqpilot.llm.provider import OpenAICompatibleProvider
from abqpilot.llm.schema import validate_reasoning_response


SECRET = "sk-test-secret-not-real"


def test_output_schema_validates_good_llm_json():
    validation = validate_reasoning_response(_good_payload())

    assert validation["valid"] is True
    assert validation["status"] == "PASS"


def test_output_schema_rejects_forbidden_action_recommendation():
    payload = _good_payload()
    payload["recommended_next_action"] = "Submit solver and bypass approval token."

    validation = validate_reasoning_response(payload)

    assert validation["valid"] is False
    assert "submit solver" in validation["forbidden_recommendations"]


def test_provider_with_confirm_path_calls_monkeypatched_urlopen_once(monkeypatch):
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            content = json.dumps(_good_payload())
            return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr("abqpilot.llm.provider.urllib.request.urlopen", fake_urlopen)
    provider = OpenAICompatibleProvider(
        LlmConfig(
            enabled=True,
            provider="chatanywhere",
            model="deepseek-chat",
            api_key=SECRET,
            chat_url="https://example.invalid/v1/chat/completions",
        )
    )

    result = provider.reason({"task_id": "task", "safety_boundaries": {"solver_submit_allowed": False}})

    assert len(calls) == 1
    assert result["validation"]["valid"] is True
    assert SECRET not in json.dumps(result)


def test_rejected_output_writes_safety_validation_artifact(tmp_path):
    payload = _good_payload()
    payload["recommended_next_action"] = "Start QueueRunner."
    validation = validate_reasoning_response(payload)
    payload["validation"] = validation

    paths = write_reasoning_artifacts(tmp_path, {"task_id": "task"}, payload, {"provider": "mock", "api_key": SECRET})

    safety = json.loads(open(paths["llm_safety_validation"], encoding="utf-8").read())
    metadata = json.loads(open(paths["llm_request_metadata"], encoding="utf-8").read())
    raw = open(paths["llm_reasoning_raw_response"], encoding="utf-8").read()

    assert safety["valid"] is False
    assert "api_key" not in metadata
    assert "Authorization" not in metadata
    assert SECRET not in raw


def _good_payload():
    return {
        "schema_version": "0.1",
        "provider": "chatanywhere",
        "model": "deepseek-chat",
        "verdict": "WAITING",
        "observation": "The queued job has not produced ODB evidence yet.",
        "diagnosis": "AbqPilot should remain at the read-only monitoring boundary.",
        "recommended_next_action": "Poll JobPilot Status",
        "allowed_actions": ["poll_jobpilot_status", "export_run_report"],
        "blocked_actions": ["submit_solver", "start_queue_runner"],
        "risk_flags": [],
        "human_review_required": True,
        "confidence": 0.8,
    }
