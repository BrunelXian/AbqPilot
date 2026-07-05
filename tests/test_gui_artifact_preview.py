from pathlib import Path

from abqpilot.gui.artifact_preview import ArtifactPreviewState, build_artifact_preview


def test_artifact_preview_module_imports() -> None:
    assert ArtifactPreviewState.READY.value == "ARTIFACT_PREVIEW_READY"


def test_artifact_preview_missing_and_unsupported_are_read_only(tmp_path: Path) -> None:
    missing = build_artifact_preview(tmp_path / "missing.md")
    assert missing["parse_status"] == "ARTIFACT_PREVIEW_MISSING_FILE"
    assert missing["read_only"] is True
    unsupported_path = tmp_path / "artifact.bin"
    unsupported_path.write_bytes(b"abc")
    unsupported = build_artifact_preview(unsupported_path)
    assert unsupported["parse_status"] == "ARTIFACT_PREVIEW_UNSUPPORTED_TYPE"
    assert unsupported["unsupported_reason"] == "UNSUPPORTED_READ_ONLY_PREVIEW"
    assert unsupported["mutation_allowed"] is False


def test_artifact_preview_never_allows_execution_or_final_approval(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('{"status":"READY"}', encoding="utf-8")
    preview = build_artifact_preview(path)
    assert preview["execution_allowed"] is False
    assert preview["external_open_allowed"] is False
    assert preview["final_evidence_approved"] is False
    assert preview["final_verdict_frozen"] is False
