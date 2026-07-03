from abqpilot.gui.action_controller import GuiActionController


def test_gui_job_diagnosis_action_imports():
    controller = GuiActionController(project_root=".")

    assert callable(controller.diagnose_job_output)

