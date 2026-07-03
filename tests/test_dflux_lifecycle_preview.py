from abqpilot.patching.dflux_lifecycle_preview import (
    compare_successful_failed_2x,
    preview_dflux_deactivation_patch_stage,
)


def _inp() -> str:
    return "\n".join(
        [
            "*Heading",
            "*Step, name=step_scan_00",
            "*Coupled Temperature-displacement",
            "0.05, 1.",
            "*Dflux",
            "inst_plate.set-body-1, BF, 2e+10",
            "*Output, field",
            "NT, U",
            "*End Step",
            "*Step, name=Step_cool_00",
            "*Coupled Temperature-displacement",
            "0.1, 100.",
            "*Output, field",
            "NT, U",
            "*End Step",
            "",
        ]
    )


def test_stage_preview_writes_artifacts_and_passes(tmp_path):
    source = tmp_path / "source.inp"
    source.write_text(_inp(), encoding="utf-8")

    result = preview_dflux_deactivation_patch_stage(source, output_dir=tmp_path / "out")

    assert result["verdict"] == "DFLUX_DEACTIVATION_PATCH_PREVIEW_READY"
    assert result["details"]["cooling_step_has_dflux_op_new"] is True
    assert result["details"]["unrelated_changes_count"] == 0
    assert (tmp_path / "out" / "dflux_lifecycle_patch_plan.json").exists()


def test_successful_comparison_handles_missing_files(tmp_path):
    result = compare_successful_failed_2x(tmp_path / "missing", tmp_path / "failed.inp")

    assert result["successful_2x_job_file_comparison_available"] is False
