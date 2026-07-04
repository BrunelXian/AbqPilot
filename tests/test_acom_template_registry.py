from __future__ import annotations

import pytest

from abqpilot.acom.template_registry import get_template, list_templates, validate_template_pack


REQUIRED = {
    "stage_implementation",
    "read_only_audit",
    "guarded_candidate_preview",
    "controlled_execution_planning",
    "job_odb_diagnosis_review",
    "mcpguard_review",
    "abqjobpilot_record_audit",
    "docs_status_update",
    "test_expansion",
    "safety_secret_audit",
}


def test_all_10_required_templates_are_registered() -> None:
    assert {template.template_id for template in list_templates()} == REQUIRED


def test_unknown_template_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        get_template("unknown_template")


def test_high_risk_execution_templates_are_not_registered() -> None:
    for template_id in (
        "automatic_solver_run",
        "automatic_solver_retry",
        "automatic_queue_enqueue",
        "automatic_codex_execution",
        "direct_odb_metrics_extraction",
        "source_cae_mutation",
        "source_inp_mutation",
    ):
        with pytest.raises(ValueError):
            get_template(template_id)


def test_mcpguard_template_requirements() -> None:
    assert get_template("guarded_candidate_preview").requires_mcpguard is True
    assert get_template("mcpguard_review").requires_mcpguard is True


def test_template_pack_validates() -> None:
    assert validate_template_pack()["verdict"] == "ACOM_TEMPLATE_PACK_VALID"
