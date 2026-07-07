from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash


def test_candidate_hash_computes_sha256_for_allowed_candidate(tmp_path) -> None:
    candidate = tmp_path / "candidate.inp"
    candidate.write_text("*Heading\n", encoding="utf-8")
    result = compute_candidate_artifact_hash(candidate)
    assert result["algorithm"] == "SHA256"
    assert result["exists"] is True
    assert result["hash"]
    assert result["blocked_reason"] is None


def test_candidate_hash_blocks_forbidden_paths(tmp_path) -> None:
    for name in (".env", "source_sanity_base.inp", "job.odb", "queue.json"):
        path = tmp_path / name
        path.write_text("blocked", encoding="utf-8")
        result = compute_candidate_artifact_hash(path)
        assert result["hash"] is None
        assert result["blocked_reason"]
