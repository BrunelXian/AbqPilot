import json
from pathlib import Path

from abqpilot import cli
from abqpilot.reporting.project_status import export_project_status


def test_project_status_file_generation(tmp_path):
    result = export_project_status(root=tmp_path)

    assert result["verdict"] == "PROJECT_STATUS_EXPORTED"
    assert Path(result["output_paths"]["project_status_json"]).exists()
    assert Path(result["output_paths"]["project_status_md"]).exists()
    payload = json.loads(Path(result["output_paths"]["project_status_json"]).read_text(encoding="utf-8"))
    assert payload["gui_status"] == "GUI Beta safe workflow cockpit"
    assert "10_compare_metrics" in payload["current_pipeline_order"]


def test_export_project_status_cli_command(tmp_path):
    result = cli.command_export_project_status(root=tmp_path)

    assert result["success"] is True
    assert Path(result["output_paths"]["project_status_md"]).exists()
