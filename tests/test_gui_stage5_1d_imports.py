def test_stage5_1d_preview_modules_and_gui_app_import() -> None:
    import abqpilot.gui.app  # noqa: F401
    import abqpilot.gui.artifact_preview  # noqa: F401
    import abqpilot.gui.artifact_type_classifier  # noqa: F401
    import abqpilot.gui.json_preview  # noqa: F401
    import abqpilot.gui.markdown_preview  # noqa: F401
    import abqpilot.gui.preview_safety  # noqa: F401
    import abqpilot.gui.report_viewer  # noqa: F401
    import abqpilot.gui.section_extractor  # noqa: F401


def test_stage5_1d_report_viewer_copy_is_non_executing() -> None:
    from abqpilot.gui.report_viewer import CLAIM_BOUNDARY_NOTICE, READ_ONLY_NOTICE, SAFETY_BOUNDARY_NOTICE

    assert "Read-only preview" in READ_ONLY_NOTICE
    assert "Final evidence remains locked" in CLAIM_BOUNDARY_NOTICE
    assert "Solver / ODB / metrics remain disabled" in SAFETY_BOUNDARY_NOTICE
    assert "flagged, not fixed" in SAFETY_BOUNDARY_NOTICE
