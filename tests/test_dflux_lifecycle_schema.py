from abqpilot.patching.dflux_lifecycle_schema import build_patch_plan, validate_patch_plan


def test_patch_schema_validates_dflux_deactivation_reset(tmp_path):
    plan = build_patch_plan("source.inp", "preview.inp", "step_scan_00", "Step_cool_00", "load_body_hflux_00")

    result = validate_patch_plan(plan)

    assert result["valid"] is True


def test_patch_schema_rejects_forbidden_scope_omission():
    plan = build_patch_plan("source.inp", "preview.inp", "step_scan_00", "Step_cool_00", "load_body_hflux_00")
    plan["forbidden_scopes"] = ["material"]

    result = validate_patch_plan(plan)

    assert result["valid"] is False


def test_patch_schema_requires_no_apply_or_solver():
    plan = build_patch_plan("source.inp", "preview.inp", "step_scan_00", "Step_cool_00", "load_body_hflux_00")
    plan["apply_repair_now"] = True
    plan["run_solver_now"] = True

    result = validate_patch_plan(plan)

    assert result["valid"] is False
