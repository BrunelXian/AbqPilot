from __future__ import annotations

from pathlib import Path

from abqpilot.pipeline_protocol.agent_registry import AGENTS


ROOT = Path(__file__).resolve().parents[1]


def test_each_agent_has_required_contract_files_and_phrases() -> None:
    for agent in AGENTS:
        base = ROOT / "agents" / agent.slug
        for name in ("AGENTS.md", "INPUT_CONTRACT.md", "OUTPUT_CONTRACT.md"):
            path = base / name
            assert path.exists(), path
        text = (base / "AGENTS.md").read_text(encoding="utf-8")
        assert "Codex/LLM summary is not final evidence" in text or "Codex summary is not final evidence" in text


def test_templates_have_required_sections() -> None:
    template_dir = ROOT / "docs" / "templates" / "pipeline_task"
    run_template = (template_dir / "RUN_REPORT_TEMPLATE.md").read_text(encoding="utf-8")
    for section in (
        "Purpose",
        "Inputs",
        "Actions Taken",
        "Outputs",
        "Validation",
        "Guardrails / Forbidden Actions Confirmation",
        "Verdict",
        "Claim Boundary",
        "Next Recommended Step",
    ):
        assert section in run_template
    handoff_template = (template_dir / "HANDOFF_TEMPLATE.md").read_text(encoding="utf-8")
    for section in (
        "Context",
        "Inputs for Receiver",
        "Required Task",
        "Allowed Actions",
        "Forbidden Actions",
        "Required Outputs",
        "Acceptance Criteria",
        "Gate Requirement",
    ):
        assert section in handoff_template
    gate_template = (template_dir / "GATE_TEMPLATE.md").read_text(encoding="utf-8")
    for section in (
        "Transition",
        "Risk Level",
        "Required Conditions",
        "Evidence Reviewed",
        "Decision",
        "Approver",
        "Reason",
        "Residual Risk",
    ):
        assert section in gate_template


def test_docs_mention_pipeline_style_not_hierarchy_and_root_rules() -> None:
    architecture = (ROOT / "docs" / "PIPELINE_AGENT_ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "pipeline-style" in architecture
    assert "not a hierarchical" in architecture
    root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "HANDOFF_XXX.md" in root_agents
    assert "RUN_XXX.md" in root_agents
    assert "GATE_XXX.md" in root_agents
