from pathlib import Path


def test_gui_beta_modules_import_without_launching_window():
    from abqpilot.gui.action_controller import GuiActionController
    from abqpilot.gui.app import AbqPilotGui, main
    from abqpilot.gui.artifact_viewer import preview_artifact
    from abqpilot.gui.task_loader import discover_recent_tasks

    assert callable(main)
    assert GuiActionController is not None
    assert AbqPilotGui is not None
    assert callable(preview_artifact)
    assert callable(discover_recent_tasks)


def test_gui_beta_code_has_no_forbidden_runtime_calls():
    gui_dir = Path("abqpilot/gui")
    source = "\n".join(path.read_text(encoding="utf-8") for path in gui_dir.glob("*.py"))
    forbidden = [
        "run_next_job",
        "waitForCompletion",
        "openOdb",
        "session.openOdb",
        "LangGraph",
        "subprocess",
        "Popen",
        "os.system",
    ]

    assert not any(token in source for token in forbidden)
