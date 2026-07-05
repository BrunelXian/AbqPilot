from pathlib import Path

from abqpilot.gui.report_viewer import build_report_viewer_card, render_report_viewer_text


def test_report_viewer_card_has_read_only_and_boundary_copy(tmp_path: Path) -> None:
    path = tmp_path / "report.md"
    path.write_text(
        """# Report

## Claim Boundary
Non-final.

## Safety Boundary
No solver.
""",
        encoding="utf-8",
    )
    card = build_report_viewer_card(path)
    text = render_report_viewer_text(card)
    assert card["read_only"] is True
    assert card["action_allowed"] is False
    assert "Read-only preview" in text
    assert "Final evidence remains locked" in text
    assert "Solver / ODB / metrics remain disabled" in text
    assert "This viewer does not modify artifacts" in text


def test_report_viewer_card_includes_unsafe_claims(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.json"
    path.write_text('{"solver_approved": true}', encoding="utf-8")
    card = build_report_viewer_card(path)
    assert card["unsafe_claims"]
    assert "BLOCKED_UNSAFE" in card["status_badge"]
