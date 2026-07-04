from __future__ import annotations

import json

from abqpilot import cli
from abqpilot.acom.result_schema import empty_structured_result


def test_cli_generate_validate_report_and_intake(tmp_path):
    generated = cli.command_generate_codex_handoff(
        task_id="cli",
        task_type="model_condition_guard_review",
        output_dir=tmp_path / "handoff",
        title="CLI handoff",
        objective="Review MCPGuard artifacts.",
    )
    assert generated["verdict"] == "ACOM_HANDOFF_GENERATED"

    validated = cli.command_validate_codex_handoff(tmp_path / "handoff")
    assert validated["verdict"] == "ACOM_HANDOFF_VALID"

    reported = cli.command_report_codex_handoff(tmp_path / "handoff")
    assert reported["verdict"] == "ACOM_HANDOFF_REPORT_READY"

    payload = empty_structured_result("cli", generated["handoff_id"])
    result_path = tmp_path / "structured_result.json"
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    intake = cli.command_intake_codex_result(tmp_path / "handoff", result_path)
    assert intake["verdict"] == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"
