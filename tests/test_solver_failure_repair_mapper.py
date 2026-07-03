import json

from abqpilot.repair import propose_solver_failure_repair


def test_convergence_failure_maps_to_solver_control_proposal(tmp_path):
    _diagnosis(tmp_path, "JOB_SOLVER_CONVERGENCE_FAILED", "solver_convergence_failure", too_many_attempts=True)

    result = propose_solver_failure_repair(tmp_path)
    proposal = result["details"]

    assert result["verdict"] == "REPAIR_PROPOSAL_READY"
    assert proposal["recommended_repair_type"] == "step_increment_relaxation"
    assert "minimum_increment_reduction" in proposal["secondary_repair_types"]
    assert proposal["requires_human_review"] is True
    assert proposal["apply_repair_now"] is False
    assert proposal["run_solver_now"] is False


def test_input_processor_failure_does_not_propose_step_control_blindly(tmp_path):
    _diagnosis(tmp_path, "JOB_INPUT_PROCESSOR_FAILED", "input_processor_failure")

    result = propose_solver_failure_repair(tmp_path)

    assert result["details"]["repair_proposal_status"] == "REPAIR_PROPOSAL_MANUAL_REVIEW_ONLY"
    assert result["details"]["recommended_repair_type"] == "manual_review_required"


def test_unknown_diagnosis_blocks_unknown(tmp_path):
    _diagnosis(tmp_path, "JOB_STATUS_UNKNOWN", "unknown")

    result = propose_solver_failure_repair(tmp_path)

    assert result["details"]["repair_proposal_status"] == "REPAIR_PROPOSAL_BLOCKED_UNKNOWN_FAILURE"


def test_missing_diagnosis_blocks(tmp_path):
    result = propose_solver_failure_repair(tmp_path)

    assert result["details"]["repair_proposal_status"] == "REPAIR_PROPOSAL_BLOCKED_NO_DIAGNOSIS"


def test_failed_odb_remains_not_acceptable(tmp_path):
    _diagnosis(tmp_path, "JOB_SOLVER_CONVERGENCE_FAILED", "solver_convergence_failure", too_many_attempts=True)

    result = propose_solver_failure_repair(tmp_path)

    assert result["details"]["evidence_summary"]["odb_acceptable_for_metrics"] is False


def _diagnosis(root, status, category, too_many_attempts=False):
    payload = {
        "diagnosis_status": status,
        "failure_category": category,
        "odb_acceptable_for_metrics": False,
        "evidence": {
            "analysis_completed": False,
            "analysis_not_completed": True,
            "too_many_attempts": too_many_attempts,
            "terminated_due_to_errors": True,
        },
        "important_lines": {"msg_error_lines": ["***ERROR"], "sta_tail": ["tail"]},
        "job_name": "job",
    }
    (root / "job_odb_diagnosis_result.json").write_text(json.dumps(payload), encoding="utf-8")

