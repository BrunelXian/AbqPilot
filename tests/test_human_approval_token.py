from pathlib import Path

from abqpilot.gui.human_approval_token import (
    ACKNOWLEDGEMENT_FLAGS,
    SOLVER_APPROVAL_PHRASE,
    TOKEN_TYPE,
    build_controlled_solver_approval_token_schema,
)


def test_human_approval_token_schema_contains_required_fields(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.inp"
    candidate.write_text("*Heading\n", encoding="utf-8")
    token = build_controlled_solver_approval_token_schema("task", tmp_path, candidate, SOLVER_APPROVAL_PHRASE)
    assert token["token_type"] == TOKEN_TYPE
    assert token["candidate_artifact_hash"]
    assert token["approval_phrase_required"] == SOLVER_APPROVAL_PHRASE
    assert set(token["acknowledgement_flags"]) == set(ACKNOWLEDGEMENT_FLAGS)
    assert token["active_approval"] is False
    assert token["preview_only_in_stage_5_2b"] is True
