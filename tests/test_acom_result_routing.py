from __future__ import annotations

from abqpilot.acom.result_routing import handoff_agent_token, route_for_template


def test_required_template_routes() -> None:
    assert route_for_template("mcpguard_review")["primary_downstream_agent"] == "GuardAgent"
    assert route_for_template("docs_status_update")["primary_downstream_agent"] == "DocsStatusAgent"
    assert route_for_template("test_expansion")["primary_downstream_agent"] == "SoftwareQAAgent"
    assert route_for_template("job_odb_diagnosis_review")["primary_downstream_agent"] == "DiagnosisAgent"
    assert route_for_template("guarded_candidate_preview")["downstream_agents"] == ["CandidateBuilderAgent", "GuardAgent"]
    assert route_for_template("stage_implementation")["downstream_agents"] == ["SoftwareQAAgent", "DocsStatusAgent"]


def test_handoff_agent_token_uses_readable_agent_suffix() -> None:
    assert handoff_agent_token("GuardAgent") == "GUARD_AGENT"
    assert handoff_agent_token("DocsStatusAgent") == "DOCS_STATUS_AGENT"
    assert handoff_agent_token("SoftwareQAAgent") == "SOFTWARE_QA_AGENT"
