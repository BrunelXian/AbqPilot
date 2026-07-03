from abqpilot.guards.model_condition_guard import run_model_condition_guard


def test_mcp_guard_passes_fixed_candidate(tmp_path):
    jnl, source, candidate = _files(tmp_path, fixed=True)

    result = run_model_condition_guard(jnl, source, candidate, declared_target_changes=[_target()], output_dir=tmp_path / "out")

    assert result["verdict"] == "MCP_GUARD_PASS"
    assert result["details"]["guard_status"] == "MCP_PASS"
    assert (tmp_path / "out" / "model_condition_preservation_result.json").exists()


def test_mcp_guard_fails_old_candidate(tmp_path):
    jnl, source, candidate = _files(tmp_path, fixed=False)

    result = run_model_condition_guard(jnl, source, candidate, declared_target_changes=[_target()], output_dir=tmp_path / "out")

    assert result["verdict"] == "MCP_GUARD_FAIL_CONDITION_LOSS"
    assert result["details"]["eligible_for_solver"] is False


def _files(tmp_path, fixed: bool):
    jnl = tmp_path / "model.jnl"
    source = tmp_path / "source.inp"
    candidate = tmp_path / "candidate.inp"
    jnl.write_text(
        "mdb.models['Model-1'].CoupledTempDisplacementStep(name='step_scan_00', previous='Initial')\n"
        "mdb.models['Model-1'].CoupledTempDisplacementStep(name='Step_cool_00', previous='step_scan_00')\n"
        "mdb.models['Model-1'].BodyHeatFlux(createStepName='step_scan_00', magnitude=10000000000.0, name='load_body_hflux_00', region=r)\n"
        "mdb.models['Model-1'].loads['load_body_hflux_00'].deactivate('Step_cool_00')\n",
        encoding="utf-8",
    )
    source.write_text(_inp("1e+10", True), encoding="utf-8")
    candidate.write_text(_inp("2e+10", fixed), encoding="utf-8")
    return jnl, source, candidate


def _inp(value: str, op_new: bool) -> str:
    cooling = "*Dflux, OP=NEW\n" if op_new else ""
    return f"*Step, name=step_scan_00\n*Dflux\ninst_plate.set-body-1, BF, {value}\n*End Step\n*Step, name=Step_cool_00\n{cooling}*End Step\n"


def _target():
    return {"type": "body_heat_flux_magnitude", "load_name": "load_body_hflux_00", "step": "step_scan_00", "from": "1e+10", "to": "2e+10"}
