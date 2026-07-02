from abqpilot.llm.patch_proposal_schema import safe_patch_proposal, validate_patch_proposal


def test_schema_accepts_valid_no_action():
    proposal = safe_patch_proposal("NO_ACTION", "No repair required.", "no_action")

    assert validate_patch_proposal(proposal)["valid"] is True


def test_schema_accepts_allowed_heat_flux_proposal():
    proposal = safe_patch_proposal(
        "PATCH_PROPOSED",
        "A future guarded heat flux adjustment may be useful.",
        "heat_flux_magnitude_adjustment",
        operation="propose_guarded_scale_review",
        target="heat_flux_magnitude",
    )

    assert validate_patch_proposal(proposal)["valid"] is True


def test_schema_rejects_forbidden_patch_types():
    for patch_type in [
        "material_change",
        "geometry_change",
        "mesh_change",
        "solver_submit",
        "queue_runner_launch",
        "direct_odb_open",
        "raw_inp_edit",
    ]:
        proposal = safe_patch_proposal("PATCH_PROPOSED", "bad", "no_action")
        proposal["candidate_patch"]["patch_type"] = patch_type

        assert validate_patch_proposal(proposal)["valid"] is False


def test_schema_rejects_guard_requirement_false():
    proposal = safe_patch_proposal("PATCH_PROPOSED", "guard missing", "heat_flux_magnitude_adjustment")
    proposal["guard_requirements"]["requires_diff_guard"] = False

    validation = validate_patch_proposal(proposal)

    assert validation["valid"] is False
    assert "guard_requirements.requires_diff_guard must be true" in validation["errors"]


def test_schema_rejects_forbidden_rationale_text():
    proposal = safe_patch_proposal("PATCH_PROPOSED", "submit solver after editing inp", "heat_flux_magnitude_adjustment")

    validation = validate_patch_proposal(proposal)

    assert validation["valid"] is False
    assert "submit solver" in validation["forbidden_terms"]
