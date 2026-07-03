from abqpilot.guards.model_condition_compare import LOSS_CODE, compare_model_conditions


def test_compare_passes_fixed_candidate():
    result = compare_model_conditions(_intent(), _inp_rep(1e10, True), _inp_rep(2e10, True), None, [_target()])

    assert result["guard_status"] == "MCP_PASS"
    assert result["target_patch_isolation"]["status"] == "PASS"
    assert result["condition_findings"][0]["status"] == "PRESERVED"


def test_compare_fails_missing_cooling_reset():
    result = compare_model_conditions(_intent(), _inp_rep(1e10, True), _inp_rep(2e10, False), None, [_target()])

    assert result["guard_status"] == "MCP_FAIL_CONDITION_LOSS"
    assert result["condition_findings"][0]["finding_code"] == LOSS_CODE


def test_target_patch_isolation_flags_unauthorized_extra_change():
    result = compare_model_conditions(_intent(), _inp_rep(1e10, True), _inp_rep(3e10, True), None, [_target()])

    assert result["guard_status"] == "MCP_FAIL_UNAUTHORIZED_CONDITION_CHANGE"
    assert result["target_patch_isolation"]["status"] == "FAIL"


def test_missing_source_intent_requires_review():
    result = compare_model_conditions({"loads": []}, _inp_rep(1e10, True), _inp_rep(2e10, True), None, [_target()])

    assert result["guard_status"] == "MCP_REVIEW_REQUIRED"


def _intent():
    return {
        "loads": [
            {
                "name": "load_body_hflux_00",
                "kind": "BodyHeatFlux",
                "created_step": "step_scan_00",
                "deactivated_steps": ["Step_cool_00"],
            }
        ]
    }


def _target():
    return {"type": "body_heat_flux_magnitude", "load_name": "load_body_hflux_00", "step": "step_scan_00", "from": "1e+10", "to": "2e+10"}


def _inp_rep(value, op_new):
    return {
        "steps": [
            {"name": "step_scan_00", "dflux": {"positive_bf_lines": [{"value": value}], "has_dflux_op_new": False}},
            {"name": "Step_cool_00", "dflux": {"positive_bf_lines": [], "has_dflux_op_new": op_new, "keywords": [{"line": 1, "text": "*Dflux, OP=NEW"}] if op_new else []}},
        ]
    }
