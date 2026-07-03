from abqpilot import cli


def test_cli_preview_dflux_deactivation_patch(tmp_path):
    source = tmp_path / "source.inp"
    source.write_text(
        "\n".join(
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
        ),
        encoding="utf-8",
    )

    result = cli.command_preview_dflux_deactivation_patch(source_inp=source, output_dir=tmp_path / "out")

    assert result["verdict"] == "DFLUX_DEACTIVATION_PATCH_PREVIEW_READY"
    assert result["details"]["source_inp_unchanged"] is True
    assert result["details"]["run_solver_now"] is False


def test_cli_parser_accepts_dflux_preview_command():
    args = cli.build_parser().parse_args(
        [
            "preview-dflux-deactivation-patch",
            "--source-inp",
            "source.inp",
            "--scan-step",
            "step_scan_00",
            "--cooling-step",
            "Step_cool_00",
        ]
    )

    assert args.command == "preview-dflux-deactivation-patch"
    assert args.source_inp == "source.inp"
