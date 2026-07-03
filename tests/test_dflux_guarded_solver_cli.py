from abqpilot.cli import build_parser


def test_dflux_guarded_solver_cli_commands_exist():
    commands = build_parser()._subparsers._group_actions[0].choices
    for command in [
        "prepare-dflux-guarded-solver-run",
        "approve-dflux-guarded-solver-run",
        "run-dflux-guarded-solver-approved",
        "monitor-dflux-guarded-solver-run",
        "intake-dflux-guarded-solver-output",
        "report-dflux-guarded-solver-run",
    ]:
        assert command in commands
