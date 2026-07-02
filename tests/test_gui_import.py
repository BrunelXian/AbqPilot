from pathlib import Path


def test_gui_imports_without_abqjobpilot_gui_or_dangerous_actions():
    from abqpilot.gui import app, actions, widgets  # noqa: F401

    gui_dir = Path("abqpilot/gui")
    source = "\n".join(path.read_text(encoding="utf-8") for path in gui_dir.glob("*.py"))
    forbidden = [
        "QueueRunner",
        "run_next_job",
        "run_gui",
        "waitForCompletion",
        "openOdb",
        "session.openOdb",
        "OpenAI",
        "LangGraph",
        "subprocess",
        "Popen",
        "os.system",
    ]

    assert not any(token in source for token in forbidden)


def test_gui_main_symbol_is_available():
    from abqpilot.gui.app import main

    assert callable(main)
