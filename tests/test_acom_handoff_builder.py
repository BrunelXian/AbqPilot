from __future__ import annotations

import json

from abqpilot.acom.handoff_builder import generate_codex_handoff, validate_codex_handoff
from abqpilot.acom.handoff_schema import REQUIRED_HANDOFF_FILES


def test_handoff_builder_creates_required_files(tmp_path):
    result = generate_codex_handoff(task_id="builder", task_type="model_condition_guard_review", output_dir=tmp_path / "handoff")
    assert result["success"] is True
    for file_name in REQUIRED_HANDOFF_FILES:
        assert (tmp_path / "handoff" / file_name).exists()


def test_generated_codex_task_contains_safety_and_evidence_rules(tmp_path):
    generate_codex_handoff(task_id="builder", task_type="model_condition_guard_review", output_dir=tmp_path / "handoff")
    task = (tmp_path / "handoff" / "codex_task.md").read_text(encoding="utf-8")
    assert "Safety Boundary" in task
    assert "Codex natural-language summary is not final evidence" in task
    assert "non-target original model conditions must be preserved" in task


def test_generated_safety_and_evidence_contracts(tmp_path):
    generate_codex_handoff(task_id="builder", task_type="model_condition_guard_review", output_dir=tmp_path / "handoff")
    safety = json.loads((tmp_path / "handoff" / "safety_contract.json").read_text(encoding="utf-8"))
    flags = safety["safety_flags"]
    assert flags["solver_run_allowed"] is False
    assert flags["queue_runner_allowed"] is False
    assert flags["odb_open_allowed"] is False
    assert flags["env_read_allowed"] is False
    assert flags["source_sanity_base_mutation_allowed"] is False
    assert flags["shell_true_allowed"] is False
    assert flags["codex_cli_auto_call_allowed"] is False
    evidence = json.loads((tmp_path / "handoff" / "evidence_contract.json").read_text(encoding="utf-8"))
    assert evidence["requires_mcpguard_result_for_model_mutation_or_inp_patch"] is True


def test_validate_codex_handoff(tmp_path):
    generate_codex_handoff(task_id="builder", task_type="test_expansion", output_dir=tmp_path / "handoff")
    validation = validate_codex_handoff(tmp_path / "handoff")
    assert validation["verdict"] == "ACOM_HANDOFF_VALID"
