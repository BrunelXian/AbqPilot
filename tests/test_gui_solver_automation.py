from abqpilot.gui.action_controller import GuiActionController


def test_gui_solver_automation_actions_import():
    controller = GuiActionController(project_root=".")

    assert callable(controller.prepare_controlled_solver_run)
    assert callable(controller.approve_controlled_solver_run)
    assert callable(controller.run_approved_solver)
    assert callable(controller.monitor_solver_run)
    assert callable(controller.intake_solver_output)
    assert callable(controller.report_solver_run)

