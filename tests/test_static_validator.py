from pathlib import Path

from abqpilot.tools.static_validator_tool import StaticValidator


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "mvp1_am_thermal" / "base_heatflux_marker.inp"


def test_static_validator_passes_valid_example():
    report = StaticValidator().validate(BASE)
    assert report["passed"] is True


def test_static_validator_fails_if_nt11_missing(tmp_path):
    inp = tmp_path / "missing_nt11.inp"
    inp.write_text(BASE.read_text(encoding="utf-8").replace("NT11", ""), encoding="utf-8")
    report = StaticValidator().validate(inp)
    assert report["passed"] is False
    assert "NT11" in report["missing"]


def test_static_validator_is_case_insensitive(tmp_path):
    inp = tmp_path / "lower.inp"
    inp.write_text(BASE.read_text(encoding="utf-8").lower(), encoding="utf-8")
    report = StaticValidator().validate(inp, target_region="surf_track_001_top")
    assert report["passed"] is True

