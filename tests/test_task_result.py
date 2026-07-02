import json

from abqpilot.core.task_result import make_task_result, write_result_json


def test_make_task_result_standard_shape():
    result = make_task_result(
        command="status",
        verdict="STATUS_OK",
        success=True,
        output_paths={"report": "report.json"},
        safety_flags={"allow_llm": False},
    )
    assert result["command"] == "status"
    assert result["verdict"] == "STATUS_OK"
    assert result["success"] is True
    assert result["output_paths"]["report"] == "report.json"
    assert result["safety_flags"]["allow_llm"] is False
    assert result["warnings"] == []
    assert result["errors"] == []


def test_write_result_json_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "result.json"
    result = make_task_result("status", "STATUS_OK", True)
    write_result_json(result, path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["verdict"] == "STATUS_OK"
