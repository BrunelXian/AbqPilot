from abqpilot.cli import build_parser


def test_solver_cli_commands_exist():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices
    for command in [
        "prepare-solver-run",
        "approve-solver-run",
        "run-solver-approved",
        "monitor-solver-run",
        "intake-solver-run-output",
        "report-solver-run",
    ]:
        assert command in commands
