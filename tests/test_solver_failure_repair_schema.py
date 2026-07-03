from abqpilot.repair.solver_failure_repair_schema import validate_repair_proposal


def test_schema_rejects_forbidden_repair_type():
    proposal = _proposal()
    proposal["recommended_repair_type"] = "material_change"

    result = validate_repair_proposal(proposal)

    assert result["valid"] is False
    assert result["status"] == "REPAIR_PROPOSAL_REJECTED_BY_SCHEMA"


def test_schema_requires_human_review_and_no_execution():
    proposal = _proposal()

    result = validate_repair_proposal(proposal)

    assert result["valid"] is True


def test_schema_rejects_execution_flags():
    proposal = _proposal()
    proposal["apply_repair_now"] = True

    result = validate_repair_proposal(proposal)

    assert result["valid"] is False


def _proposal():
    return {
        "recommended_repair_type": "step_increment_relaxation",
        "secondary_repair_types": ["minimum_increment_reduction"],
        "allowed_patch_scope": ["step_incrementation_controls"],
        "requires_human_review": True,
        "apply_repair_now": False,
        "run_solver_now": False,
    }

