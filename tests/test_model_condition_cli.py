from abqpilot.cli import build_parser, command_run_model_condition_guard


def test_mcp_cli_command_exists():
    commands = build_parser()._subparsers._group_actions[0].choices
    assert "run-model-condition-guard" in commands


def test_mcp_cli_positive_and_negative(tmp_path):
    jnl = tmp_path / "model.jnl"
    source = tmp_path / "source.inp"
    fixed = tmp_path / "fixed.inp"
    old = tmp_path / "old.inp"
    jnl.write_text(
        "mdb.models['Model-1'].BodyHeatFlux(createStepName='step_scan_00', magnitude=10000000000.0, name='load_body_hflux_00', region=r)\n"
        "mdb.models['Model-1'].loads['load_body_hflux_00'].deactivate('Step_cool_00')\n",
        encoding="utf-8",
    )
    source.write_text(_inp("1e+10", True), encoding="utf-8")
    fixed.write_text(_inp("2e+10", True), encoding="utf-8")
    old.write_text(_inp("2e+10", False), encoding="utf-8")
    target = "body_heat_flux_magnitude:load_body_hflux_00:step_scan_00:1e+10:2e+10"

    positive = command_run_model_condition_guard(jnl, source, fixed, output_dir=tmp_path / "pos", target_change=target)
    negative = command_run_model_condition_guard(jnl, source, old, output_dir=tmp_path / "neg", target_change=target)

    assert positive["verdict"] == "MCP_GUARD_PASS"
    assert negative["verdict"] == "MCP_GUARD_FAIL_CONDITION_LOSS"


def _inp(value: str, op_new: bool) -> str:
    cooling = "*Dflux, OP=NEW\n" if op_new else ""
    return f"*Step, name=step_scan_00\n*Dflux\ninst_plate.set-body-1, BF, {value}\n*End Step\n*Step, name=Step_cool_00\n{cooling}*End Step\n"
