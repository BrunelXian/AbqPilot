from abqpilot.guards.model_condition_extractor import extract_inp_conditions, extract_jnl_conditions


def test_jnl_extractor_detects_body_heat_flux_creation_and_deactivate(tmp_path):
    jnl = tmp_path / "model.jnl"
    jnl.write_text(
        "mdb.models['Model-1'].CoupledTempDisplacementStep(name='step_scan_00', previous='Initial')\n"
        "mdb.models['Model-1'].CoupledTempDisplacementStep(name='Step_cool_00', previous='step_scan_00')\n"
        "mdb.models['Model-1'].BodyHeatFlux(createStepName='step_scan_00', magnitude=10000000000.0, name='load_body_hflux_00', region=r)\n"
        "mdb.models['Model-1'].loads['load_body_hflux_00'].deactivate('Step_cool_00')\n",
        encoding="utf-8",
    )

    result = extract_jnl_conditions(jnl)

    assert "step_scan_00" in result["steps"]
    load = result["loads"][0]
    assert load["kind"] == "BodyHeatFlux"
    assert load["created_step"] == "step_scan_00"
    assert load["deactivated_steps"] == ["Step_cool_00"]
    assert load["magnitude"] == 10000000000.0


def test_inp_extractor_detects_steps_bf_and_cooling_op_new(tmp_path):
    inp = tmp_path / "model.inp"
    inp.write_text(_inp(cooling_op_new=True), encoding="utf-8")

    result = extract_inp_conditions(inp)

    names = [step["name"] for step in result["steps"]]
    assert names == ["step_scan_00", "Step_cool_00"]
    scan = result["steps"][0]
    cool = result["steps"][1]
    assert scan["dflux"]["positive_bf_lines"][0]["value"] == 20000000000.0
    assert cool["dflux"]["has_dflux_op_new"] is True


def test_inp_extractor_detects_missing_cooling_reset(tmp_path):
    inp = tmp_path / "model.inp"
    inp.write_text(_inp(cooling_op_new=False), encoding="utf-8")

    cool = extract_inp_conditions(inp)["steps"][1]

    assert cool["dflux"]["has_dflux"] is False
    assert cool["dflux"]["has_dflux_op_new"] is False


def _inp(cooling_op_new: bool) -> str:
    cooling = "*Dflux, OP=NEW\n" if cooling_op_new else ""
    return (
        "*Heading\n"
        "*Step, name=step_scan_00\n"
        "*Dflux\n"
        "inst_plate.set-body-1, BF, 2e+10\n"
        "*End Step\n"
        "*Step, name=Step_cool_00\n"
        f"{cooling}"
        "*End Step\n"
    )
