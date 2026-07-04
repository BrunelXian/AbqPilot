from __future__ import annotations

from pathlib import Path

from abqpilot import cli


def test_cli_list_describe_generate_and_validate_template_pack(tmp_path, capsys) -> None:
    assert cli.main(["list-acom-templates"]) == 0
    listed = capsys.readouterr().out
    assert "stage_implementation" in listed
    assert "safety_secret_audit" in listed

    assert cli.main(["describe-acom-template", "--template-id", "mcpguard_review"]) == 0
    described = capsys.readouterr().out
    assert "template_id=mcpguard_review" in described
    assert "requires_mcpguard=True" in described
    assert "codex_auto_execution_allowed=False" in described

    task_id = "cli_template_pipeline"
    assert cli.main(["scaffold-pipeline-task", "--task-id", task_id, "--root", str(tmp_path)]) == 0
    assert cli.command_generate_codex_handoff(
        task_id=task_id,
        template_id="mcpguard_review",
        title="Template CLI smoke",
        objective="Generate integrated handoff.",
    )["success"] is True

    assert cli.main(["validate-acom-template-pack"]) == 0
    validated = capsys.readouterr().out
    assert "ACOM_TEMPLATE_PACK_VALID" in validated


def test_cli_generate_template_id_writes_real_project_task(tmp_path) -> None:
    result = cli.command_generate_codex_handoff(
        task_id="command_template",
        template_id="mcpguard_review",
        title="Command template",
        objective="Command smoke",
    )
    assert result["success"] is True
    assert Path(result["run_record_path"]).exists()
    assert Path(result["pipeline_handoff_path"]).exists()
