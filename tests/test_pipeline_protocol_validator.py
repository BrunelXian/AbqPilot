from __future__ import annotations

from pathlib import Path

from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_protocol_validator_passes_scaffolded_task(tmp_path) -> None:
    result = scaffold_pipeline_task("valid_task", root=tmp_path)
    validation = validate_task_protocol(result["task_dir"])
    assert validation["verdict"] == "PIPELINE_PROTOCOL_VALID"


def test_protocol_validator_rejects_missing_run_file(tmp_path) -> None:
    result = scaffold_pipeline_task("missing_run", root=tmp_path)
    task_dir = Path(result["task_dir"])
    (task_dir / "trace" / "RUN_001_INTAKE.md").unlink()
    validation = validate_task_protocol(task_dir)
    assert validation["verdict"] == "PIPELINE_PROTOCOL_INVALID"
    assert any("RUN_001_INTAKE.md" in error for error in validation["errors"])


def test_protocol_validator_rejects_missing_handoff_file(tmp_path) -> None:
    result = scaffold_pipeline_task("missing_handoff", root=tmp_path)
    task_dir = Path(result["task_dir"])
    (task_dir / "handoffs" / "HANDOFF_001_INTAKE_TO_AUDIT.md").unlink()
    validation = validate_task_protocol(task_dir)
    assert validation["verdict"] == "PIPELINE_PROTOCOL_INVALID"
    assert any("HANDOFF_001_INTAKE_TO_AUDIT.md" in error for error in validation["errors"])


def test_protocol_validator_rejects_missing_gate_file(tmp_path) -> None:
    result = scaffold_pipeline_task("missing_gate", root=tmp_path)
    task_dir = Path(result["task_dir"])
    (task_dir / "gates" / "GATE_001_ALLOW_CANDIDATE_BUILD.md").unlink()
    validation = validate_task_protocol(task_dir)
    assert validation["verdict"] == "PIPELINE_PROTOCOL_INVALID"
    assert any("GATE_001_ALLOW_CANDIDATE_BUILD.md" in error for error in validation["errors"])
