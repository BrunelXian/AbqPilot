import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_governance_docs_exist():
    assert (PROJECT_ROOT / "AGENTS.md").exists()
    assert (PROJECT_ROOT / "ABQPILOT.md").exists()
    assert (PROJECT_ROOT / "docs" / "architecture" / "ABQPILOT_CODEX_INTEGRATION_STRATEGY.md").exists()


def test_tool_permissions_json_exists_and_is_valid():
    path = PROJECT_ROOT / "configs" / "tool_permissions.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == "0.1"


def test_codex_is_not_runtime_authority():
    permissions = _permissions()
    codex = permissions["codex"]
    assert codex["allowed_as_development_assistant"] is True
    assert codex["allowed_as_runtime_agent"] is False
    assert codex["allowed_to_submit_abaqus_jobs"] is False
    assert codex["allowed_to_modify_cae"] is False
    assert codex["allowed_to_open_odb"] is False


def test_llm_and_solver_runtime_are_disabled():
    permissions = _permissions()
    assert permissions["llm"]["enabled"] is False
    assert permissions["llm"]["allowed_to_submit_abaqus_jobs"] is False
    assert permissions["abaqus"]["allow_solver_submit"] is False


def test_human_approval_contains_required_high_risk_transitions():
    approvals = set(_permissions()["human_approval_required_for"])
    assert "solver_submit" in approvals
    assert "guard_relaxation" in approvals


def test_governance_docs_contain_codex_policy_phrase():
    combined = "\n".join(
        [
            (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            (PROJECT_ROOT / "ABQPILOT.md").read_text(encoding="utf-8"),
            (
                PROJECT_ROOT
                / "docs"
                / "architecture"
                / "ABQPILOT_CODEX_INTEGRATION_STRATEGY.md"
            ).read_text(encoding="utf-8"),
        ]
    )
    assert "Use Codex to build AbqPilot" in combined
    assert "Do not make Codex the agent" in combined


def _permissions() -> dict:
    return json.loads((PROJECT_ROOT / "configs" / "tool_permissions.json").read_text(encoding="utf-8"))
