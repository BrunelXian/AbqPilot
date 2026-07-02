from pathlib import Path

from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder
from abqpilot.tools.diff_guard_tool import DiffGuard


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "mvp1_am_thermal" / "base_heatflux_marker.inp"


def _copy_base(tmp_path) -> Path:
    path = tmp_path / "base.inp"
    path.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _mutate_line(source: Path, target: Path, old: str, new: str) -> None:
    target.write_text(source.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def test_diff_guard_rejects_material_change(tmp_path):
    base = _copy_base(tmp_path)
    gen = tmp_path / "generated.inp"
    _mutate_line(base, gen, "*Material, name=STEEL_FIXTURE", "*Material, name=ALUMINUM_FIXTURE")
    report = DiffGuard().compare(base, gen)
    assert report["allowed"] is False
    assert report["forbidden_changed"] is True


def test_diff_guard_rejects_node_change(tmp_path):
    base = _copy_base(tmp_path)
    gen = tmp_path / "generated.inp"
    _mutate_line(base, gen, "2, 1.0, 0.0, 0.0", "2, 2.0, 0.0, 0.0")
    report = DiffGuard().compare(base, gen)
    assert report["forbidden_changed"] is True
    assert report["allowed"] is False


def test_diff_guard_rejects_element_change(tmp_path):
    base = _copy_base(tmp_path)
    gen = tmp_path / "generated.inp"
    _mutate_line(base, gen, "1, 1, 2, 3, 4, 5, 6, 7, 8", "1, 1, 2, 3, 4, 5, 6, 7, 7")
    report = DiffGuard().compare(base, gen)
    assert report["forbidden_changed"] is True
    assert report["allowed"] is False


def test_diff_guard_rejects_boundary_change(tmp_path):
    base = _copy_base(tmp_path)
    gen = tmp_path / "generated.inp"
    _mutate_line(base, gen, "1, 11, 11, 20.0", "1, 11, 11, 30.0")
    report = DiffGuard().compare(base, gen)
    assert report["forbidden_changed"] is True
    assert report["allowed"] is False


def test_diff_guard_rejects_forbidden_section_line_edit(tmp_path):
    base = _copy_base(tmp_path)
    gen = tmp_path / "generated.inp"
    _mutate_line(base, gen, "210000., 0.3", "200000., 0.3")
    report = DiffGuard().compare(base, gen)
    assert report["forbidden_changed"] is True
    assert report["allowed"] is False


def test_diff_guard_allows_marker_heat_flux_magnitude_only_change(tmp_path):
    base = _copy_base(tmp_path)
    gen = tmp_path / "generated.inp"
    status = HeatFluxPatchBuilder().build(
        {
            "base_inp_path": str(base),
            "generated_inp_path": str(gen),
            "parameters": {"heat_flux_scale": 1.1},
        }
    )
    report = DiffGuard().compare(base, gen)
    assert status["allowed"] is True
    assert report["allowed"] is True
    assert report["forbidden_changed"] is False
    assert report["uncertainty"] is False

