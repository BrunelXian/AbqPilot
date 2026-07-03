from pathlib import Path

from abqpilot.patching.dflux_lifecycle_patch import (
    preview_dflux_deactivation_patch,
    validate_dflux_lifecycle,
)


def _inp() -> str:
    return "\n".join(
        [
            "*Heading",
            "** STEP: step_scan_00",
            "*Step, name=step_scan_00, nlgeom=YES",
            "*Coupled Temperature-displacement",
            "0.05, 1., 1e-99, 0.1",
            "*Dflux",
            "inst_plate.set-body-1, BF, 2e+10",
            "*Output, field",
            "*Node Output",
            "NT, U",
            "*End Step",
            "** STEP: Step_cool_00",
            "*Step, name=Step_cool_00, nlgeom=YES",
            "*Coupled Temperature-displacement",
            "0.1, 100., 1e-30, 10.",
            "*Output, field",
            "*Node Output",
            "NT, U",
            "*End Step",
            "",
        ]
    )


def test_preview_builder_inserts_op_new_and_preserves_source(tmp_path):
    source = tmp_path / "source.inp"
    preview = tmp_path / "preview.inp"
    source.write_text(_inp(), encoding="utf-8")
    before = source.read_text(encoding="utf-8")

    result = preview_dflux_deactivation_patch(source, preview)

    assert result["allowed"] is True
    assert "*Dflux, OP=NEW" in preview.read_text(encoding="utf-8")
    assert source.read_text(encoding="utf-8") == before


def test_preview_builder_preserves_scan_step_bf_and_no_positive_cooling_bf(tmp_path):
    source = tmp_path / "source.inp"
    preview = tmp_path / "preview.inp"
    source.write_text(_inp(), encoding="utf-8")
    preview_dflux_deactivation_patch(source, preview)

    validation = validate_dflux_lifecycle(source, preview)

    assert validation["passed"] is True
    assert validation["scan_step_bf_preserved"] is True
    assert validation["cooling_step_positive_bf_lines"] == 0
    assert validation["unrelated_changes_count"] == 0


def test_preview_builder_idempotent_if_op_new_exists(tmp_path):
    source = tmp_path / "source.inp"
    preview = tmp_path / "preview.inp"
    text = _inp()
    first = text.find("*Output, field")
    second = text.find("*Output, field", first + 1)
    source.write_text(text[:second] + "*Dflux, OP=NEW\n" + text[second:], encoding="utf-8")

    result = preview_dflux_deactivation_patch(source, preview)

    assert result["allowed"] is True
    assert result["inserted_lines_count"] == 0


def test_preview_builder_blocks_missing_cooling_step(tmp_path):
    source = tmp_path / "source.inp"
    preview = tmp_path / "preview.inp"
    source.write_text(_inp().replace("Step_cool_00", "OtherStep"), encoding="utf-8")

    result = preview_dflux_deactivation_patch(source, preview)

    assert result["allowed"] is False
    assert "cooling step not found" in result["errors"][0]


def test_preview_builder_blocks_missing_scan_dflux(tmp_path):
    source = tmp_path / "source.inp"
    preview = tmp_path / "preview.inp"
    source.write_text(_inp().replace("*Dflux\ninst_plate.set-body-1, BF, 2e+10\n", ""), encoding="utf-8")

    result = preview_dflux_deactivation_patch(source, preview)

    assert result["allowed"] is False
    assert "scan-step DFLUX/BF load not found" in result["errors"]
