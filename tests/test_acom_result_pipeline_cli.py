from __future__ import annotations

import json
from pathlib import Path

from abqpilot import cli
from abqpilot.acom.result_schema import empty_structured_result


def test_cli_intake_and_report_acom_result(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    task_id = "cli_acom_result_intake"

    assert cli.main(["scaffold-pipeline-task", "--task-id", task_id, "--root", str(tmp_path)]) == 0
    assert cli.main(
        [
            "generate-codex-handoff",
            "--task-id",
            task_id,
            "--template-id",
            "mcpguard_review",
            "--title",
            "CLI ACOM result intake",
            "--objective",
            "Generate a pipeline handoff for intake CLI testing.",
        ]
    ) == 0

    task_dir = tmp_path / "runs" / "tasks" / task_id
    manifest = json.loads((task_dir / "codex_handoff" / "handoff_manifest.json").read_text(encoding="utf-8"))
    result_path = task_dir / "codex_result" / "structured_result.json"
    result_path.write_text(
        json.dumps(empty_structured_result(task_id, manifest["handoff_id"]), indent=2),
        encoding="utf-8",
    )

    assert cli.main(["intake-codex-result", "--handoff-dir", str(task_dir / "codex_handoff"), "--result-json", str(result_path)]) == 0
    intake_output = capsys.readouterr().out
    assert "intake_status=ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION" in intake_output
    assert "downstream_agent=GuardAgent" in intake_output
    assert "gate_decision=PENDING_REVALIDATION" in intake_output

    assert cli.main(["report-acom-result-intake", "--task-dir", str(task_dir)]) == 0
    report_output = capsys.readouterr().out
    assert "ACOM_RESULT_INTAKE_REPORT_READY" in report_output


def test_cli_unsafe_acom_result_rejected(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    task_id = "cli_acom_result_unsafe"
    assert cli.main(["generate-codex-handoff", "--task-id", task_id, "--template-id", "mcpguard_review"]) == 0
    task_dir = tmp_path / "runs" / "tasks" / task_id
    manifest = json.loads((task_dir / "codex_handoff" / "handoff_manifest.json").read_text(encoding="utf-8"))
    payload = empty_structured_result(task_id, manifest["handoff_id"])
    payload["safety_flags"]["solver_started"] = True
    result_path = task_dir / "codex_result" / "structured_result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert cli.main(["intake-codex-result", "--handoff-dir", str(task_dir / "codex_handoff"), "--result-json", str(result_path)]) == 1
    output = capsys.readouterr().out
    assert "intake_status=ACOM_RESULT_REJECTED_SAFETY_FLAGS" in output
    assert "unsafe_safety_flags=solver_started" in output
