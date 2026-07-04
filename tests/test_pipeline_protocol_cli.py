from __future__ import annotations

from pathlib import Path

from abqpilot import cli


def test_cli_list_pipeline_agents_works(capsys) -> None:
    assert cli.main(["list-pipeline-agents"]) == 0
    output = capsys.readouterr().out
    assert "PipelineSupervisor" in output
    assert "DocsStatusAgent" in output


def test_cli_scaffold_validate_and_report_pipeline_protocol(tmp_path, capsys) -> None:
    task_id = "cli_pipeline_smoke"
    root = str(tmp_path)
    assert cli.main(["scaffold-pipeline-task", "--task-id", task_id, "--root", root]) == 0
    task_dir = tmp_path / "runs" / "tasks" / task_id
    assert task_dir.exists()
    assert cli.main(["validate-pipeline-protocol", "--task-dir", str(task_dir)]) == 0
    validate_output = capsys.readouterr().out
    assert "PIPELINE_PROTOCOL_VALID" in validate_output
    assert cli.main(["report-pipeline-protocol", "--task-dir", str(task_dir)]) == 0
    report_output = capsys.readouterr().out
    assert "PIPELINE_PROTOCOL_REPORT_READY" in report_output
    assert (task_dir / "PIPELINE_PROTOCOL_REPORT.md").exists()
