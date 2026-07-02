from abqpilot.patching.patch_validation import validate_patch_preview_request


def test_unsupported_patch_type_blocks():
    proposal = _proposal("PATCH_PROPOSED", "step_time_adjustment", value=2.0)

    result = validate_patch_preview_request(proposal)

    assert result["allowed"] is False
    assert result["status"] == "PATCH_PREVIEW_BLOCKED_UNSUPPORTED_PATCH_TYPE"


def test_forbidden_patch_type_blocks_before_mutation():
    for patch_type in ["material_change", "geometry_change", "mesh_change", "solver_submit", "raw_inp_edit"]:
        proposal = _proposal("PATCH_PROPOSED", patch_type, value=1.0)

        result = validate_patch_preview_request(proposal)

        assert result["allowed"] is False
        assert result["status"] == "PATCH_PREVIEW_BLOCKED_NO_VALID_PROPOSAL"


def test_heat_flux_requires_positive_numeric_scale():
    proposal = _proposal("PATCH_PROPOSED", "heat_flux_magnitude_adjustment", value=None)

    result = validate_patch_preview_request(proposal)

    assert result["allowed"] is False
    assert result["status"] == "PATCH_PREVIEW_BLOCKED_TARGET_NOT_IDENTIFIED"


def _proposal(verdict, patch_type, value=None):
    return {
        "schema_version": "0.1",
        "provider": "mock",
        "model": "mock",
        "proposal_verdict": verdict,
        "rationale": "test",
        "candidate_patch": {
            "patch_type": patch_type,
            "target": "target",
            "operation": "operation",
            "value": value,
            "units": None,
            "expected_effect": "test",
            "requires_human_review": True,
        },
        "guard_requirements": {
            "requires_static_validator": True,
            "requires_diff_guard": True,
            "requires_physics_guard": True,
            "requires_human_approval": True,
        },
        "blocked_actions": [],
        "risk_flags": [],
        "confidence": 0.5,
    }
