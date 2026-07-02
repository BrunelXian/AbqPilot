from pathlib import Path

from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "mvp1_am_thermal" / "base_heatflux_marker.inp"


def _request(base: Path, out: Path, scale: float) -> dict:
    return {
        "base_inp_path": str(base),
        "generated_inp_path": str(out),
        "parameters": {"heat_flux_scale": scale},
    }


def test_heat_flux_patch_builder_only_changes_marker_magnitude(tmp_path):
    base = tmp_path / "base.inp"
    out = tmp_path / "generated.inp"
    base.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")

    status = HeatFluxPatchBuilder().build(_request(base, out, 1.25))

    assert status["allowed"] is True
    base_lines = base.read_text(encoding="utf-8").splitlines()
    out_lines = out.read_text(encoding="utf-8").splitlines()
    changed = [idx for idx, pair in enumerate(zip(base_lines, out_lines, strict=True)) if pair[0] != pair[1]]
    assert changed == [32]
    assert "1250000" in out_lines[32]


def test_heat_flux_patch_builder_fails_if_marker_missing(tmp_path):
    base = tmp_path / "base.inp"
    out = tmp_path / "generated.inp"
    text = BASE.read_text(encoding="utf-8").replace("ABQPILOT_EDITABLE_HEAT_FLUX_START", "REMOVED_START")
    text = text.replace("ABQPILOT_EDITABLE_HEAT_FLUX_END", "REMOVED_END")
    base.write_text(text, encoding="utf-8")

    status = HeatFluxPatchBuilder().build(_request(base, out, 1.1))

    assert status["allowed"] is False
    assert not out.exists()


def test_heat_flux_patch_builder_fails_if_multiple_markers(tmp_path):
    base = tmp_path / "base.inp"
    out = tmp_path / "generated.inp"
    text = BASE.read_text(encoding="utf-8")
    marker = "\n** ABQPILOT_EDITABLE_HEAT_FLUX_START id=HF_EXTRA\n*Dsflux\nSURF_TRACK_001_TOP, S, 1.0\n** ABQPILOT_EDITABLE_HEAT_FLUX_END id=HF_EXTRA\n"
    base.write_text(text + marker, encoding="utf-8")

    status = HeatFluxPatchBuilder().build(_request(base, out, 1.1))

    assert status["allowed"] is False


def test_heat_flux_patch_builder_fails_if_scale_non_positive(tmp_path):
    base = tmp_path / "base.inp"
    out = tmp_path / "generated.inp"
    base.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")

    status = HeatFluxPatchBuilder().build(_request(base, out, 0))

    assert status["allowed"] is False
    assert "positive" in status["errors"][0]

