from abqpilot.gui.action_controller import GuiActionController


def test_gui_patch_queue_actions_import(tmp_path):
    controller = GuiActionController(project_root=tmp_path)

    assert hasattr(controller, "queue_patch_preview_preflight")
    assert hasattr(controller, "queue_patch_preview_dry_run")
    assert hasattr(controller, "create_patch_queue_approval_token")
    assert hasattr(controller, "queue_patch_preview_real_queue_only")
    assert hasattr(controller, "poll_patch_queue_status")


def test_gui_patch_queue_missing_task_returns_safe_error(tmp_path):
    controller = GuiActionController(project_root=tmp_path)

    result = controller.queue_patch_preview_preflight(tmp_path / "missing")

    assert result["success"] is False
    assert result["verdict"] == "PATCH_TO_QUEUE_BLOCKED_INVALID_PREVIEW"
