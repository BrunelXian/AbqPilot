from __future__ import annotations

from pathlib import Path

from abqpilot.acom.non_solver_revalidation_profiles import run_profile_checks, summarize_checks


def test_software_qa_profile_warns_if_tests_not_run(tmp_path):
    checks = run_profile_checks(
        "SoftwareQAAgent",
        task_dir=tmp_path,
        scaffold={},
        intake={"result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"},
        structured_result={"safety_flags": {}, "validation_claims": {}, "tests_run": [], "artifacts": {}},
    )
    summary = summarize_checks(checks)
    assert any("test result summary" in item for item in summary["warning_items"])


def test_software_qa_profile_fails_unsafe_flag(tmp_path):
    checks = run_profile_checks(
        "SoftwareQAAgent",
        task_dir=tmp_path,
        scaffold={},
        intake={"result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"},
        structured_result={"safety_flags": {"solver_started": True}, "validation_claims": {}, "tests_run": [], "artifacts": {}},
    )
    summary = summarize_checks(checks)
    assert any("unsafe safety flags" in item for item in summary["fail_items"])


def test_docs_status_profile_reads_project_status():
    checks = run_profile_checks(
        "DocsStatusAgent",
        task_dir=Path("."),
        scaffold={},
        intake={"result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"},
        structured_result={"safety_flags": {}, "files_created": [], "files_modified": []},
    )
    summary = summarize_checks(checks)
    assert not any("PROJECT_STATUS_CURRENT.json valid JSON" in item for item in summary["fail_items"])
