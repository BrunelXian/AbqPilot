import json

from abqpilot.core.artifact_registry import ArtifactRegistry


def test_artifact_registry_add_get_save_load(tmp_path):
    source = tmp_path / "source.inp"
    source.write_text("*Heading\n", encoding="utf-8")
    registry = ArtifactRegistry("task_001")
    artifact = registry.add_artifact("source_inp", "input", source, None)

    assert artifact["exists"] is True
    assert registry.get_artifact("source_inp")["path"] == str(source)

    path = tmp_path / "artifacts.json"
    registry.save(path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["task_id"] == "task_001"

    loaded = ArtifactRegistry.load(path)
    assert loaded.task_id == "task_001"
    assert loaded.get_artifact("source_inp")["exists"] is True
