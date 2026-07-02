import json

from abqpilot import cli


SECRET = "PATCH_PROPOSAL_CLI_SECRET"


def test_propose_patch_mock_writes_artifacts(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task = _task(tmp_path, repair_required=False)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli.command_propose_patch(task_dir=task, provider="mock")

    assert result["verdict"] == "NO_ACTION"
    assert result["output_paths"]["llm_candidate_patch_proposal"].endswith("llm_candidate_patch_proposal.json")
    assert SECRET not in json.dumps(result)


def test_real_provider_requires_confirm(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task = _task(tmp_path, repair_required=False)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli.command_propose_patch(task_dir=task, provider="chatanywhere", model="deepseek-chat")

    assert result["verdict"] == "LLM_PATCH_CONTEXT_CONFIRMATION_REQUIRED"
    assert result["details"]["sent_patch_context"] is False


def test_confirmed_real_provider_monkeypatched(monkeypatch, tmp_path):
    _write_env(tmp_path)
    task = _task(tmp_path, repair_required=False)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    calls = []

    def fake_propose(self, context):
        calls.append(context)
        return {
            "schema_version": "0.1",
            "provider": "chatanywhere",
            "model": "deepseek-chat",
            "proposal_verdict": "NO_ACTION",
            "rationale": "No patch required.",
            "candidate_patch": {
                "patch_type": "no_action",
                "target": "none",
                "operation": "none",
                "value": None,
                "units": None,
                "expected_effect": "No mutation.",
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
            "validation": {"valid": True, "status": "PASS", "errors": [], "forbidden_terms": []},
        }

    monkeypatch.setattr("abqpilot.llm.patch_proposal_reasoner.OpenAICompatiblePatchProposalReasoner.propose", fake_propose)

    result = cli.command_propose_patch(
        task_dir=task,
        provider="chatanywhere",
        model="deepseek-chat",
        confirm_send_patch_context=True,
    )

    assert len(calls) == 1
    assert result["verdict"] == "NO_ACTION"
    assert result["details"]["sent_patch_context"] is True
    assert SECRET not in json.dumps(result)
    metadata = open(result["output_paths"]["llm_patch_request_metadata"], encoding="utf-8").read()
    raw = open(result["output_paths"]["llm_patch_raw_response"], encoding="utf-8").read()
    assert "Authorization" not in metadata
    assert SECRET not in raw


def test_cli_parser_accepts_propose_patch():
    parser = cli.build_parser()
    args = parser.parse_args(["propose-patch", "--task-dir", "task", "--provider", "mock"])

    assert args.command == "propose-patch"
    assert args.provider == "mock"


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


def _task(tmp_path, repair_required):
    task = tmp_path / "runs" / "tasks" / "task"
    task.mkdir(parents=True)
    (task / "task_state.json").write_text(json.dumps({"task_id": "task", "status": "PASS", "failed_steps": []}), encoding="utf-8")
    (task / "artifacts.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    analysis = task / "analysis"
    analysis.mkdir()
    (analysis / "repair_plan.json").write_text(
        json.dumps(
            {
                "evaluation_verdict": "PASS",
                "repair_required": repair_required,
                "recommended_next_action": "Export Run Report",
                "allowed_patch_types": ["heat_flux_magnitude_adjustment"],
                "forbidden_patch_types": ["material_change"],
            }
        ),
        encoding="utf-8",
    )
    return task
