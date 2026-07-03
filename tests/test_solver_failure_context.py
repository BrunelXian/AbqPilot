import json

from abqpilot.repair.solver_failure_context import build_solver_failure_context


def test_context_excludes_full_inp_and_odb_content(tmp_path):
    diagnosis = {
        "diagnosis_status": "JOB_SOLVER_CONVERGENCE_FAILED",
        "failure_category": "solver_convergence_failure",
        "odb_acceptable_for_metrics": False,
        "evidence": {"too_many_attempts": True},
        "important_lines": {"msg_error_lines": ["***ERROR"], "sta_tail": ["tail"]},
        "job_name": "job",
    }
    (tmp_path / "job_odb_diagnosis_result.json").write_text(json.dumps(diagnosis), encoding="utf-8")
    (tmp_path / "solver_preflight_result.json").write_text(
        json.dumps({"candidate_inp_path": "candidate.inp", "candidate_traceability": "sanity-base-derived"}),
        encoding="utf-8",
    )

    context = build_solver_failure_context(tmp_path)

    assert context["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"
    assert context["candidate_traceability"] == "sanity-base-derived"
    assert context["contains_full_inp_content"] is False
    assert context["contains_odb_content"] is False
    assert context["contains_env_secret"] is False

