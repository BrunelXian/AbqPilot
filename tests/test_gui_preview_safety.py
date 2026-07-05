from abqpilot.gui.preview_safety import find_unsafe_claims, has_unsafe_claims


def test_preview_safety_flags_all_required_unsafe_claims() -> None:
    keys = [
        "final_evidence_approved",
        "final_verdict_frozen",
        "solver_approved",
        "odb_metrics_approved",
        "codex_summary_is_final_evidence",
        "solver_run",
        "queue_runner_launched",
        "odb_opened",
        "codex_cli_called",
        "shell_true_used",
    ]
    for key in keys:
        claims = find_unsafe_claims({key: True}, path="artifact.json")
        assert claims and claims[0]["key"] == key
        assert has_unsafe_claims({key: True})
