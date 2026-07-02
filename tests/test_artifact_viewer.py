import json

from abqpilot.gui.artifact_viewer import preview_artifact


def test_artifact_viewer_previews_json(tmp_path):
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps({"b": 2, "a": 1}), encoding="utf-8")

    result = preview_artifact(path)

    assert result["status"] == "ARTIFACT_PREVIEW_READY"
    assert '"a": 1' in result["preview"]


def test_artifact_viewer_previews_markdown_and_text(tmp_path):
    path = tmp_path / "report.md"
    path.write_text("# Report\n\nHello", encoding="utf-8")

    result = preview_artifact(path)

    assert result["previewable"] is True
    assert "# Report" in result["preview"]


def test_artifact_viewer_truncates_large_text(tmp_path):
    path = tmp_path / "large.txt"
    path.write_text("x" * 64, encoding="utf-8")

    result = preview_artifact(path, max_bytes=8)

    assert result["truncated"] is True
    assert "Preview truncated" in result["preview"]


def test_artifact_viewer_path_only_for_unknown_or_binary(tmp_path):
    path = tmp_path / "model.odb"
    path.write_bytes(b"\x00\x01\x02")

    result = preview_artifact(path)

    assert result["status"] == "ARTIFACT_PATH_ONLY"
    assert result["previewable"] is False
    assert str(path) in result["preview"]
