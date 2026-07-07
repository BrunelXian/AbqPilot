from abqpilot.gui.controlled_solver_dry_run_request_card import build_controlled_solver_dry_run_request_card


def test_dry_run_request_card_copy(tmp_path) -> None:
    card = build_controlled_solver_dry_run_request_card(tmp_path)
    assert card["title"] == "Controlled Solver Dry-Run Request [NO EXECUTION]"
    assert card["dry_run_only"] is True
    assert card["request_active"] is False
    assert card["solver_execution_allowed"] is False
    assert card["queue_entry_created"] is False
    assert card["backend_callback"] is None
    copy = "\n".join(card["safety_notes"])
    assert "not an active solver_request.json" in copy
    assert "No queue entry is created" in copy
    assert "Final evidence remains locked" in copy
