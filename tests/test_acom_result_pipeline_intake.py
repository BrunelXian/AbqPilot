from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.result_pipeline_intake import intake_pipeline_acom_result
from abqpilot.acom.result_schema import empty_structured_result
from abqpilot.acom.template_renderer import render_pipeline_acom_handoff
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


def _pipeline_handoff(tmp_path: Path, template_id: str = "mcpguard_review") -> dict:
    return render_pipeline_acom_handoff(
        task_id=f"intake_{template_id}",
        template_id=template_id,
        project_root=tmp_path,
        title="Result intake smoke",
        objective="Generate a pipeline-integrated handoff for intake testing.",
    )


def _write_result(task_dir: Path, task_id: str, handoff_id: str, **flag_overrides: bool) -> Path:
    result_dir = task_dir / "codex_result"
    result_dir.mkdir(parents=True, exist_ok=True)
    payload = empty_structured_result(task_id, handoff_id)
    for key, value in flag_overrides.items():
        payload["safety_flags"][key] = value
    result_path = result_dir / "structured_result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result_path


def test_safe_pipeline_result_is_accepted_pending_revalidation(tmp_path) -> None:
    handoff = _pipeline_handoff(tmp_path)
    task_dir = Path(handoff["task_dir"])
    result_path = _write_result(task_dir, handoff["task_id"], handoff["handoff_id"])

    result = intake_pipeline_acom_result(handoff["handoff_dir"], result_path)

    assert result["verdict"] == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"
    details = result["details"]
    assert details["accepted_as_evidence"] is False
    assert details["gate_decision"] == "PENDING_REVALIDATION"
    assert details["downstream_agent"] == "GuardAgent"
    assert Path(details["run_record_path"]).exists()
    assert Path(details["gate_path"]).exists()
    assert Path(details["downstream_handoff_path"]).exists()
    assert load_frontmatter(details["run_record_path"])["doc_type"] == "run_report"
    assert load_frontmatter(details["gate_path"])["decision"] == "PENDING_REVALIDATION"
    assert validate_task_protocol(task_dir)["verdict"] == "PIPELINE_PROTOCOL_VALID"


def test_unsafe_pipeline_result_is_rejected_and_gate_blocked(tmp_path) -> None:
    handoff = _pipeline_handoff(tmp_path)
    task_dir = Path(handoff["task_dir"])
    result_path = _write_result(task_dir, handoff["task_id"], handoff["handoff_id"], solver_started=True)

    result = intake_pipeline_acom_result(handoff["handoff_dir"], result_path)

    assert result["verdict"] == "ACOM_RESULT_REJECTED_SAFETY_FLAGS"
    assert result["success"] is False
    details = result["details"]
    assert "solver_started" in details["unsafe_safety_flags"]
    assert load_frontmatter(details["gate_path"])["decision"] == "BLOCKED"
    assert "APPROVED" not in Path(details["gate_path"]).read_text(encoding="utf-8")


def test_pipeline_result_rejects_odb_and_env_safety_flags(tmp_path) -> None:
    for flag in ["odb_opened", "env_read"]:
        handoff = _pipeline_handoff(tmp_path, template_id="read_only_audit")
        task_dir = Path(handoff["task_dir"])
        result_path = _write_result(task_dir, handoff["task_id"], handoff["handoff_id"], **{flag: True})
        result = intake_pipeline_acom_result(handoff["handoff_dir"], result_path)
        assert result["verdict"] == "ACOM_RESULT_REJECTED_SAFETY_FLAGS"
        assert flag in result["details"]["unsafe_safety_flags"]


def test_pipeline_result_rejects_task_and_handoff_mismatches(tmp_path) -> None:
    handoff = _pipeline_handoff(tmp_path)
    task_dir = Path(handoff["task_dir"])
    result_path = _write_result(task_dir, "wrong_task", handoff["handoff_id"])
    assert intake_pipeline_acom_result(handoff["handoff_dir"], result_path)["verdict"] == "ACOM_RESULT_REJECTED_TASK_MISMATCH"

    result_path = _write_result(task_dir, handoff["task_id"], "wrong_handoff")
    assert intake_pipeline_acom_result(handoff["handoff_dir"], result_path)["verdict"] == "ACOM_RESULT_REJECTED_HANDOFF_MISMATCH"


def test_pipeline_result_blocks_missing_result_and_missing_handoff(tmp_path) -> None:
    handoff = _pipeline_handoff(tmp_path)
    missing_result = Path(handoff["task_dir"]) / "codex_result" / "missing.json"
    result = intake_pipeline_acom_result(handoff["handoff_dir"], missing_result)
    assert result["verdict"] == "ACOM_RESULT_BLOCKED_MISSING_RESULT"

    missing_handoff = intake_pipeline_acom_result(tmp_path / "missing_handoff", missing_result)
    assert missing_handoff["verdict"] == "ACOM_RESULT_BLOCKED_MISSING_HANDOFF"


def test_pipeline_result_blocks_missing_claimed_artifacts(tmp_path) -> None:
    handoff = _pipeline_handoff(tmp_path, template_id="docs_status_update")
    task_dir = Path(handoff["task_dir"])
    payload = empty_structured_result(handoff["task_id"], handoff["handoff_id"])
    payload["artifacts"] = {"audit_report": "artifacts/missing_report.md"}
    result_path = task_dir / "codex_result" / "structured_result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = intake_pipeline_acom_result(handoff["handoff_dir"], result_path)

    assert result["verdict"] == "ACOM_RESULT_BLOCKED_MISSING_ARTIFACTS"
    assert result["details"]["gate_decision"] == "BLOCKED"


def test_pipeline_result_rejects_declared_files_outside_allowed_paths(tmp_path) -> None:
    handoff = _pipeline_handoff(tmp_path, template_id="read_only_audit")
    task_dir = Path(handoff["task_dir"])
    payload = empty_structured_result(handoff["task_id"], handoff["handoff_id"])
    payload["files_modified"] = [r"C:\outside_abqpilot\unexpected.txt"]
    result_path = task_dir / "codex_result" / "structured_result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = intake_pipeline_acom_result(handoff["handoff_dir"], result_path)

    assert result["verdict"] == "ACOM_RESULT_REJECTED_SAFETY_FLAGS"
    assert "declared_path_outside_allowed_paths" in result["details"]["unsafe_safety_flags"]
