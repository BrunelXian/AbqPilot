from __future__ import annotations

import json

from abqpilot.acom.handoff_builder import generate_codex_handoff
from abqpilot.acom.result_intake import intake_codex_result
from abqpilot.acom.result_schema import empty_structured_result


def test_result_intake_blocks_missing_result_json(tmp_path):
    generate_codex_handoff(task_id="task", task_type="documentation_update", output_dir=tmp_path / "handoff")
    result = intake_codex_result(tmp_path / "handoff", tmp_path / "missing.json")
    assert result["verdict"] == "ACOM_RESULT_BLOCKED_MISSING_RESULT"


def test_result_intake_blocks_unsafe_result_json(tmp_path):
    handoff = generate_codex_handoff(task_id="task", task_type="documentation_update", output_dir=tmp_path / "handoff")
    payload = empty_structured_result("task", handoff["handoff_id"])
    payload["safety_flags"]["solver_started"] = True
    result_path = tmp_path / "structured_result.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    result = intake_codex_result(tmp_path / "handoff", result_path)
    assert result["verdict"] == "ACOM_RESULT_REJECTED_SAFETY_FLAGS"


def test_result_intake_accepts_safe_placeholder_pending_revalidation(tmp_path):
    handoff = generate_codex_handoff(task_id="task", task_type="documentation_update", output_dir=tmp_path / "handoff")
    payload = empty_structured_result("task", handoff["handoff_id"])
    result_path = tmp_path / "structured_result.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    result = intake_codex_result(tmp_path / "handoff", result_path)
    assert result["verdict"] == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"
    assert result["details"]["abqpilot_revalidation_required"] is True
    assert result["details"]["accepted_as_evidence"] is False
