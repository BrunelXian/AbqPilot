from abqpilot.gui.action_controller import GuiActionController


def test_gui_abqjobpilot_diagnosis_actions_import():
    controller = GuiActionController(".")

    assert callable(controller.list_abqjobpilot_job_records)
    assert callable(controller.diagnose_from_abqjobpilot_record)
