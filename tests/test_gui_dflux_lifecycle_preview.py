from abqpilot.gui.action_controller import GuiActionController


def test_gui_dflux_lifecycle_preview_action_imports():
    controller = GuiActionController(".")

    assert callable(controller.preview_dflux_deactivation_patch)
