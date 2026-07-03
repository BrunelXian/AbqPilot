from abqpilot.gui.action_controller import GuiActionController


def test_gui_model_condition_guard_action_imports(tmp_path):
    controller = GuiActionController(tmp_path)

    assert callable(controller.run_model_condition_guard)
