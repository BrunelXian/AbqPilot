from __future__ import annotations

from abqpilot.gui.status_badges import all_badge_labels, badge
from abqpilot.gui.visual_style import BADGE_STYLES, LAYOUT_COLUMNS, visual_token


def test_visual_style_module_imports():
    assert visual_token("surface") == "panel"
    assert LAYOUT_COLUMNS["center"] == "Workflow state and timeline"


def test_status_badge_labels_include_required_set():
    labels = set(all_badge_labels())
    for label in [
        "PASS",
        "WARNING",
        "BLOCKED",
        "PENDING",
        "READY",
        "ACKNOWLEDGED",
        "LOCKED",
        "DISABLED",
        "NON_FINAL",
        "NON_SOLVER",
        "SAFE",
        "HIGH_RISK",
    ]:
        assert label in labels
        assert label in BADGE_STYLES
        assert badge(label).startswith("[")
