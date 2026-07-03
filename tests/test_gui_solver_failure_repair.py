from abqpilot.gui.action_controller import GuiActionController


def test_gui_solver_failure_repair_action_imports():
    controller = GuiActionController(project_root=".")

    assert callable(controller.propose_solver_failure_repair)

