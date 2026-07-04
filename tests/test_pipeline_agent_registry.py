from __future__ import annotations

from pathlib import Path

from abqpilot.pipeline_protocol.agent_registry import AGENTS, agent_names, validate_agent_contracts


def test_all_12_agents_are_registered() -> None:
    assert len(AGENTS) == 12
    assert agent_names() == [
        "PipelineSupervisor",
        "IntakeAgent",
        "AuditAgent",
        "CandidateBuilderAgent",
        "GuardAgent",
        "ExecutionAgent",
        "DiagnosisAgent",
        "MetricsAgent",
        "EvidenceReportAgent",
        "ACOMAgent",
        "SoftwareQAAgent",
        "DocsStatusAgent",
    ]


def test_agent_contracts_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    result = validate_agent_contracts(root)
    assert result["success"], result["missing"]
