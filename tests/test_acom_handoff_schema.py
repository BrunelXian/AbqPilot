from __future__ import annotations

from pathlib import Path

from abqpilot.acom.handoff_builder import generate_codex_handoff
from abqpilot.acom.handoff_schema import validate_handoff_manifest


def test_handoff_schema_validates_required_fields(tmp_path):
    result = generate_codex_handoff(task_id="t1", task_type="model_condition_guard_review", output_dir=tmp_path / "handoff")
    valid, errors = validate_handoff_manifest(result["details"])
    assert valid, errors


def test_handoff_schema_rejects_codex_auto_execution(tmp_path):
    result = generate_codex_handoff(task_id="t1", task_type="documentation_update", output_dir=tmp_path / "handoff")
    manifest = dict(result["details"])
    manifest["codex_auto_execution_allowed"] = True
    valid, errors = validate_handoff_manifest(manifest)
    assert not valid
    assert any("codex_auto_execution_allowed" in error for error in errors)


def test_handoff_schema_rejects_solver_or_odb_allowed(tmp_path):
    result = generate_codex_handoff(task_id="t1", task_type="documentation_update", output_dir=tmp_path / "handoff")
    manifest = dict(result["details"])
    manifest["safety_flags"] = dict(manifest["safety_flags"])
    manifest["safety_flags"]["solver_run_allowed"] = True
    manifest["safety_flags"]["odb_open_allowed"] = True
    valid, errors = validate_handoff_manifest(manifest)
    assert not valid
    assert any("solver_run_allowed" in error for error in errors)
    assert any("odb_open_allowed" in error for error in errors)


def test_handoff_schema_requires_mcpguard(tmp_path):
    result = generate_codex_handoff(task_id="t1", task_type="documentation_update", output_dir=tmp_path / "handoff")
    manifest = dict(result["details"])
    manifest["required_abqpilot_validators"] = [item for item in manifest["required_abqpilot_validators"] if item != "MCPGuard"]
    valid, errors = validate_handoff_manifest(manifest)
    assert not valid
    assert any("MCPGuard" in error for error in errors)
