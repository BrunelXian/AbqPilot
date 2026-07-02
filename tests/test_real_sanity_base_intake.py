from pathlib import Path

from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder
from abqpilot.tools.diff_guard_tool import DiffGuard
from abqpilot.tools.real_sanity_base_intake import (
    MARKER_ID,
    detect_heat_input,
    write_manual_solver_handoff,
    write_marker_base,
    write_residual_stress_metrics_plan,
)
from examples.mvp1_am_thermal.run_stage1_6b_real_exported_inp_power_x2_audit import (
    _validate_thermo_mechanical,
)


def test_detect_exactly_one_heat_input_block(tmp_path):
    inp = _write_sample(tmp_path / "one.inp")
    report = detect_heat_input(inp)
    assert report["ok"] is True
    assert report["verdict"] == "HEAT_INPUT_DETECTED"
    assert report["selected_candidate"]["keyword"] == "*Dflux"
    assert report["selected_candidate"]["original_magnitude"] == 1.0e10


def test_fail_if_no_heat_input_block_found(tmp_path):
    inp = _write_sample(tmp_path / "none.inp", heat_block="")
    report = detect_heat_input(inp)
    assert report["ok"] is False
    assert report["verdict"] == "FAIL_NO_HEAT_INPUT_FOUND"


def test_fail_if_multiple_heat_input_blocks_are_ambiguous(tmp_path):
    heat = "*Dflux\nset-1, BF, 1e+10\n*Cflux\nnode-1, 2e+3\n"
    inp = _write_sample(tmp_path / "multi.inp", heat_block=heat)
    report = detect_heat_input(inp)
    assert report["ok"] is False
    assert report["verdict"] == "FAIL_AMBIGUOUS_HEAT_INPUT_CANDIDATES"


def test_fail_if_unsupported_heat_input_format(tmp_path):
    inp = _write_sample(tmp_path / "bad.inp", heat_block="*Dflux\nset-1, BF, not_numeric\n")
    report = detect_heat_input(inp)
    assert report["ok"] is False
    assert report["verdict"] == "FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT"


def test_marker_insertion_does_not_change_magnitude(tmp_path):
    source = _write_sample(tmp_path / "source.inp")
    intake = detect_heat_input(source)
    marked = tmp_path / "base_heatflux_marker.inp"
    marker_report = write_marker_base(source, marked, intake)
    text = marked.read_text(encoding="utf-8")
    assert marker_report["ok"] is True
    assert f"ABQPILOT_EDITABLE_HEAT_FLUX_START id={MARKER_ID}" in text
    assert "set-1, BF, 1e+10" in text


def test_power_x2_generated_file_only_changes_marker_magnitude(tmp_path):
    source = _write_sample(tmp_path / "source.inp")
    base = tmp_path / "base_heatflux_marker.inp"
    generated = tmp_path / "generated_power_x2.inp"
    write_marker_base(source, base, detect_heat_input(source))
    status = _build_x2(base, generated)
    base_lines = base.read_text(encoding="utf-8").splitlines()
    generated_lines = generated.read_text(encoding="utf-8").splitlines()
    changed = [
        idx for idx, (left, right) in enumerate(zip(base_lines, generated_lines, strict=True)) if left != right
    ]
    assert status["allowed"] is True
    assert changed == [base_lines.index("set-1, BF, 1e+10")]
    assert generated_lines[changed[0]] == "set-1, BF, 2e+10"


def test_diff_guard_passes_marker_only_x2_change(tmp_path):
    source = _write_sample(tmp_path / "source.inp")
    base = tmp_path / "base_heatflux_marker.inp"
    generated = tmp_path / "generated_power_x2.inp"
    write_marker_base(source, base, detect_heat_input(source))
    _build_x2(base, generated)
    report = DiffGuard().compare(base, generated)
    assert report["allowed"] is True
    assert report["uncertainty"] is False


def test_diff_guard_rejects_material_change(tmp_path):
    source = _write_sample(tmp_path / "source.inp")
    base = tmp_path / "base_heatflux_marker.inp"
    generated = tmp_path / "generated_power_x2.inp"
    write_marker_base(source, base, detect_heat_input(source))
    _build_x2(base, generated)
    generated.write_text(
        generated.read_text(encoding="utf-8").replace("*Material, name=MAT", "*Material, name=BAD"),
        encoding="utf-8",
    )
    report = DiffGuard().compare(base, generated)
    assert report["allowed"] is False
    assert report["forbidden_changed"] is True


def test_static_validator_for_thermo_mechanical_sanity_base_requires_nt_and_s(tmp_path):
    inp = _write_sample(tmp_path / "source.inp")
    report = _validate_thermo_mechanical(inp)
    assert report["passed"] is True
    assert report["temperature_output_token"] == "NT"
    assert report["NT11_literal_present"] is False
    missing_stress = tmp_path / "missing_s.inp"
    missing_stress.write_text(inp.read_text(encoding="utf-8").replace("HFL, PEEQ, S", "HFL, PEEQ"), encoding="utf-8")
    failed = _validate_thermo_mechanical(missing_stress)
    assert failed["passed"] is False
    assert "S" in failed["missing"]


def test_residual_stress_metrics_plan_is_written(tmp_path):
    plan = write_residual_stress_metrics_plan(tmp_path / "residual_stress_metrics_plan.json")
    assert (tmp_path / "residual_stress_metrics_plan.json").exists()
    assert "S_Mises_max" in plan["final_frame_metrics"]


def test_manual_solver_handoff_is_preview_only(tmp_path):
    text = write_manual_solver_handoff(
        tmp_path / "manual_solver_handoff.md",
        tmp_path / "base_heatflux_marker.inp",
        tmp_path / "generated_power_x2.inp",
    )
    assert "PREVIEW_ONLY_NOT_EXECUTED" in text
    assert "No command in this file was executed" in text


def test_stage1_6b_code_has_no_execution_calls():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "abqpilot" / "tools" / "real_sanity_base_intake.py",
        root / "examples" / "mvp1_am_thermal" / "run_stage1_6b_real_exported_inp_power_x2_audit.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = [
        "sub" + "process",
        "Po" + "pen",
        "os." + "system",
        "shell" + "=True",
        "open" + "Odb",
        "wait" + "ForCompletion",
    ]
    assert not any(token in combined for token in forbidden)


def _build_x2(base: Path, generated: Path) -> dict:
    return HeatFluxPatchBuilder().build(
        {
            "base_inp_path": str(base),
            "generated_inp_path": str(generated),
            "parameters": {"heat_flux_scale": 2.0},
        }
    )


def _write_sample(path: Path, heat_block: str = "*Dflux\nset-1, BF, 1e+10\n") -> Path:
    text = f"""*Heading
*Material, name=MAT
*Elastic
1., 0.3
*Node
1, 0., 0., 0.
*Element, type=C3D8T
1, 1, 1, 1, 1, 1, 1, 1, 1
*Step, name=heat
*Coupled Temperature-displacement
0.05, 1.
{heat_block}*Output, field
*Node Output
NT, RF, U
*Element Output, directions=YES
HFL, PEEQ, S
*End Step
"""
    path.write_text(text, encoding="utf-8")
    return path
