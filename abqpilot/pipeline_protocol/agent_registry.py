from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    slug: str
    role: str
    kind: str
    upstream: str | None = None
    downstream: str | None = None


AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "PipelineSupervisor",
        "pipeline_supervisor",
        "Observes trace, handoff, and gate frontmatter; controls high-risk transitions; freezes final verdicts.",
        "supervisor",
    ),
    AgentDefinition("IntakeAgent", "intake_agent", "Creates task structure and intake handoff.", "pipeline", None, "AuditAgent"),
    AgentDefinition("AuditAgent", "audit_agent", "Performs read-only audit and root-cause localization.", "pipeline", "IntakeAgent", "CandidateBuilderAgent"),
    AgentDefinition(
        "CandidateBuilderAgent",
        "candidate_builder_agent",
        "Builds copied candidates or previews and declares target change and forbidden scope.",
        "pipeline",
        "AuditAgent",
        "GuardAgent",
    ),
    AgentDefinition("GuardAgent", "guard_agent", "Runs static, diff, physics, and model-condition guards.", "pipeline", "CandidateBuilderAgent", "ExecutionAgent"),
    AgentDefinition(
        "ExecutionAgent",
        "execution_agent",
        "Executes only approved controlled operations through existing gated paths.",
        "pipeline",
        "GuardAgent",
        "DiagnosisAgent",
    ),
    AgentDefinition("DiagnosisAgent", "diagnosis_agent", "Reads job records and diagnoses ODB acceptability.", "pipeline", "ExecutionAgent", "MetricsAgent"),
    AgentDefinition("MetricsAgent", "metrics_agent", "Runs gated metrics extraction after diagnosis acceptance.", "pipeline", "DiagnosisAgent", "EvidenceReportAgent"),
    AgentDefinition(
        "EvidenceReportAgent",
        "evidence_report_agent",
        "Aggregates traces, handoffs, gates, validators, diagnosis, metrics, and limitations.",
        "pipeline",
        "MetricsAgent",
        None,
    ),
    AgentDefinition("ACOMAgent", "acom_agent", "Generates and validates Codex handoff packages as a support pathway.", "support"),
    AgentDefinition("SoftwareQAAgent", "software_qa_agent", "Runs tests and software safety audits.", "support"),
    AgentDefinition("DocsStatusAgent", "docs_status_agent", "Updates documentation and status files.", "support"),
)


def agent_names() -> list[str]:
    return [agent.name for agent in AGENTS]


def agent_contract_paths(root: str | Path | None = None) -> dict[str, dict[str, Path]]:
    base = Path(root) if root is not None else PROJECT_ROOT
    return {
        agent.name: {
            "AGENTS": base / "agents" / agent.slug / "AGENTS.md",
            "INPUT_CONTRACT": base / "agents" / agent.slug / "INPUT_CONTRACT.md",
            "OUTPUT_CONTRACT": base / "agents" / agent.slug / "OUTPUT_CONTRACT.md",
        }
        for agent in AGENTS
    }


def validate_agent_contracts(root: str | Path | None = None) -> dict[str, Any]:
    paths = agent_contract_paths(root)
    missing: list[str] = []
    for contract_set in paths.values():
        for path in contract_set.values():
            if not path.exists():
                missing.append(str(path))
    return {
        "verdict": "PIPELINE_AGENT_CONTRACTS_VALID" if not missing else "PIPELINE_AGENT_CONTRACTS_MISSING",
        "success": not missing,
        "agent_count": len(AGENTS),
        "agents": [agent.__dict__ for agent in AGENTS],
        "missing": missing,
    }
