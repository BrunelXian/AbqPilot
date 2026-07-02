import json

from abqpilot.core.task_workspace import DEFAULT_STEP_NAMES, TaskWorkspace


def test_task_workspace_creates_expected_directory_structure(tmp_path):
    workspace = TaskWorkspace(_config(tmp_path), task_id="demo_task_001").create()

    assert workspace.task_dir == tmp_path / "tasks" / "demo_task_001"
    assert workspace.config_path.exists()
    assert workspace.state_path.exists()
    assert workspace.artifacts_path.exists()
    assert workspace.trace_path.exists()
    for step_name in DEFAULT_STEP_NAMES:
        assert workspace.step_dir(step_name).exists()


def test_explicit_task_id_produces_deterministic_path(tmp_path):
    workspace = TaskWorkspace(_config(tmp_path), task_id="fixed_id").create()
    assert str(workspace.task_dir).endswith("tasks\\fixed_id") or str(workspace.task_dir).endswith("tasks/fixed_id")


def test_task_state_json_is_written(tmp_path):
    workspace = TaskWorkspace(_config(tmp_path), task_id="state_id").create()
    state = json.loads(workspace.state_path.read_text(encoding="utf-8"))
    assert state["task_id"] == "state_id"
    assert state["status"] == "CREATED"
    assert state["stop_reason"] is None
    assert state["steps"]["01_export_cae"]["status"] == "PENDING"
    assert state["steps"]["01_export_cae"]["rerun_count"] == 0
    assert state["safety_flags"]["allow_solver_submit"] is False
    assert state["safety_flags"]["allow_llm"] is False
    assert state["safety_flags"]["allow_codex_runtime"] is False


def _config(tmp_path):
    cae = tmp_path / "model.cae"
    cae.write_bytes(b"placeholder")
    return {
        "task_name": "sanity_base_heat_input_x2",
        "cae_path": str(cae),
        "work_root": str(tmp_path),
        "abaqus_command": "disabled",
        "allow_cae_export": False,
        "cae_export_mode": "write_input_only",
        "allow_odb_read": False,
        "odb_read_mode": "disabled",
        "allow_solver_submit": False,
        "allow_abqjobpilot": False,
        "allow_llm": False,
        "allow_cae_modify": False,
        "heat_input_scale": 2.0,
    }
