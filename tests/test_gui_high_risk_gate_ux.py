from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui.action_panels import build_high_risk_gate_panel
from abqpilot.gui.app import AbqPilotGui
from abqpilot.gui.high_risk_gate_ux import build_high_risk_gate_ux


def test_high_risk_gate_ux_preview_is_not_approved_or_executable() -> None:
    preview = build_high_risk_gate_ux("CONTROLLED_SOLVER_RUN")
    assert preview["approval_status"] == "NOT_APPROVED"
    assert preview["execution_status"] == "NOT_EXECUTABLE"
    assert preview["real_gate_created"] is False
    assert preview["auto_execute_allowed"] is False
    assert preview["current_allowed"] is False
    assert preview["executable"] is False
    assert "Preview only; not an approval" in preview["required_copy"]
    assert "Final evidence remains locked" in preview["required_copy"]


def test_high_risk_gate_panel_is_preview_only_and_callback_free() -> None:
    panel = build_high_risk_gate_panel()
    assert panel["preview_only"] is True
    assert panel["actions"]
    assert all(action["allowed"] is False for action in panel["actions"])
    assert all(action["executable"] is False for action in panel["actions"])
    assert all(action["backend_method"] is None for action in panel["actions"])


def test_gui_controller_imports_high_risk_preview_actions(tmp_path) -> None:
    controller = GuiActionController(tmp_path)
    catalog = controller.high_risk_gate_catalog()
    preview = controller.high_risk_gate_preview("RUN_CODEX_FROM_GUI")
    assert catalog["verdict"] == "GUI_HIGH_RISK_GATE_CATALOG_READY"
    assert preview["details"]["codex_cli_called"] is False


def test_gui_app_imports() -> None:
    assert AbqPilotGui is not None
