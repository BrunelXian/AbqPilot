from abqpilot.gui.action_controller import GuiActionController


def test_gui_dflux_guarded_solver_actions_import(tmp_path):
    controller = GuiActionController(tmp_path)
    for name in [
        "prepare_dflux_guarded_solver_run",
        "approve_dflux_guarded_solver_run",
        "run_dflux_guarded_solver_approved",
        "monitor_dflux_guarded_solver_run",
        "intake_dflux_guarded_solver_output",
        "report_dflux_guarded_solver_run",
    ]:
        assert callable(getattr(controller, name))
