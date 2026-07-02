import json

from abqpilot.llm.config import LlmConfig
from abqpilot.llm.patch_proposal_reasoner import MockPatchProposalReasoner, OpenAICompatiblePatchProposalReasoner


SECRET = "sk-patch-test-secret-not-real"


def test_mock_proposal_returns_no_action_when_no_repair_required():
    context = {
        "deterministic_repair_plan": {"repair_required": False},
        "evaluation": {"verdict": "PASS"},
    }

    proposal = MockPatchProposalReasoner().propose(context)

    assert proposal["proposal_verdict"] == "NO_ACTION"
    assert proposal["candidate_patch"]["patch_type"] == "no_action"
    assert proposal["validation"]["valid"] is True


def test_real_patch_proposal_uses_monkeypatched_provider(monkeypatch):
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            content = json.dumps(
                {
                    "schema_version": "0.1",
                    "provider": "chatanywhere",
                    "model": "deepseek-chat",
                    "proposal_verdict": "NO_ACTION",
                    "rationale": "No repair required.",
                    "candidate_patch": {
                        "patch_type": "no_action",
                        "target": "none",
                        "operation": "none",
                        "value": None,
                        "units": None,
                        "expected_effect": "No patch.",
                        "requires_human_review": True,
                    },
                    "guard_requirements": {
                        "requires_static_validator": True,
                        "requires_diff_guard": True,
                        "requires_physics_guard": True,
                        "requires_human_approval": True,
                    },
                    "blocked_actions": ["solver_submit"],
                    "risk_flags": [],
                    "confidence": 0.8,
                }
            )
            return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr("abqpilot.llm.patch_proposal_reasoner.urllib.request.urlopen", fake_urlopen)
    reasoner = OpenAICompatiblePatchProposalReasoner(
        LlmConfig(
            enabled=True,
            provider="chatanywhere",
            model="deepseek-chat",
            api_key=SECRET,
            chat_url="https://example.invalid/v1/chat/completions",
        )
    )

    proposal = reasoner.propose({"allowed_patch_types": ["no_action"], "forbidden_patch_types": ["solver_submit"]})

    assert len(calls) == 1
    assert proposal["validation"]["valid"] is True
    assert SECRET not in json.dumps(proposal)
