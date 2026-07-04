from __future__ import annotations

from abqpilot.acom.revalidation_profiles import agent_for_template, profile_for_agent


def test_template_routes_to_expected_agents():
    assert agent_for_template("mcpguard_review") == "GuardAgent"
    assert agent_for_template("docs_status_update") == "DocsStatusAgent"
    assert agent_for_template("test_expansion") == "SoftwareQAAgent"
    assert agent_for_template("job_odb_diagnosis_review") == "DiagnosisAgent"
    assert agent_for_template("read_only_audit") == "AuditAgent"
    assert agent_for_template("controlled_execution_planning") == "PipelineSupervisor"


def test_guard_profile_contains_mcpguard_original_condition_checks():
    profile = profile_for_agent("GuardAgent")
    assert profile is not None
    joined = "\n".join(profile.checklist)
    assert "MCPGuard" in joined
    assert "original model condition preservation" in joined


def test_candidate_builder_profile_requires_copied_candidate_checks():
    profile = profile_for_agent("CandidateBuilderAgent")
    assert profile is not None
    joined = "\n".join(profile.checklist)
    assert "source artifacts unchanged" in joined
    assert "copied" in joined
