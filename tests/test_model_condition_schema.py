from abqpilot.guards.model_condition_schema import MCP_PASS, parse_target_change, validate_mcp_result


def test_schema_validates_mcp_result():
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 4.5",
        "guard_name": "Model Condition Preservation Guard",
        "guard_short_name": "MCPGuard",
        "guard_status": MCP_PASS,
        "condition_findings": [],
        "requires_human_review": True,
    }

    assert validate_mcp_result(payload)["valid"] is True


def test_schema_rejects_unknown_guard_status():
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 4.5",
        "guard_name": "Model Condition Preservation Guard",
        "guard_short_name": "MCPGuard",
        "guard_status": "NOPE",
        "condition_findings": [],
        "requires_human_review": True,
    }

    assert validate_mcp_result(payload)["valid"] is False


def test_parse_target_change():
    parsed = parse_target_change("body_heat_flux_magnitude:load_body_hflux_00:step_scan_00:1e+10:2e+10")

    assert parsed["type"] == "body_heat_flux_magnitude"
    assert parsed["load_name"] == "load_body_hflux_00"
    assert parsed["from"] == "1e+10"
