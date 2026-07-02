import json

import pytest

from abqpilot.core.task_config import TaskConfigError, load_task_config, safety_flags


def test_load_task_config_uses_safe_defaults():
    config = load_task_config()
    assert config["allow_cae_export"] is False
    assert config["allow_odb_read"] is False
    assert config["allow_solver_submit"] is False
    assert config["allow_abqjobpilot"] is False
    assert config["allow_abqjobpilot_preflight"] is False
    assert config["allow_abqjobpilot_dry_run_enqueue"] is False
    assert config["allow_jobpilot_enqueue_authorization"] is False
    assert config["allow_abqjobpilot_real_enqueue"] is False
    assert config["allow_llm"] is False


def test_load_task_config_reads_json_and_validates_metrics_only(tmp_path):
    path = tmp_path / "task.json"
    path.write_text(
        json.dumps(
            {
                "allow_cae_export": True,
                "cae_export_mode": "write_input_only",
                "allow_odb_read": True,
                "odb_read_mode": "metrics_only",
                "allow_solver_submit": False,
                "allow_abqjobpilot": False,
                "allow_abqjobpilot_preflight": True,
                "allow_abqjobpilot_dry_run_enqueue": True,
                "allow_jobpilot_enqueue_authorization": True,
                "allow_abqjobpilot_real_enqueue": False,
                "allow_llm": False,
                "allow_cae_modify": False,
                "heat_input_scale": 2.0,
            }
        ),
        encoding="utf-8",
    )
    config = load_task_config(path)
    assert config["allow_cae_export"] is True
    assert config["odb_read_mode"] == "metrics_only"
    assert config["allow_abqjobpilot_preflight"] is True
    assert config["allow_abqjobpilot_dry_run_enqueue"] is True
    assert config["allow_jobpilot_enqueue_authorization"] is True
    assert config["allow_abqjobpilot"] is False
    assert config["allow_abqjobpilot_real_enqueue"] is False
    assert safety_flags(config)["allow_solver_submit"] is False


def test_abqjobpilot_dry_run_enqueue_can_be_enabled_while_real_abqjobpilot_is_disabled(tmp_path):
    path = tmp_path / "task.json"
    path.write_text(
        json.dumps(
            {
                "allow_cae_export": False,
                "cae_export_mode": "write_input_only",
                "allow_odb_read": False,
                "odb_read_mode": "disabled",
                "allow_solver_submit": False,
                "allow_abqjobpilot": False,
                "allow_abqjobpilot_preflight": True,
                "allow_abqjobpilot_dry_run_enqueue": True,
                "allow_jobpilot_enqueue_authorization": True,
                "allow_abqjobpilot_real_enqueue": False,
                "allow_llm": False,
                "allow_cae_modify": False,
                "abqjobpilot": {"allow_solver_submit": False, "submission_mode": "preview_only"},
            }
        ),
        encoding="utf-8",
    )

    config = load_task_config(path)

    assert config["allow_abqjobpilot"] is False
    assert config["allow_abqjobpilot_preflight"] is True
    assert config["allow_abqjobpilot_dry_run_enqueue"] is True
    assert config["allow_jobpilot_enqueue_authorization"] is True


def test_task_config_allows_real_abqjobpilot_enqueue_gate_when_solver_submit_stays_disabled():
    config = load_task_config(None, {"allow_abqjobpilot_real_enqueue": True})

    assert config["allow_abqjobpilot_real_enqueue"] is True
    assert config["allow_solver_submit"] is False


def test_task_config_rejects_solver_submission():
    with pytest.raises(TaskConfigError):
        load_task_config(None, {"allow_solver_submit": True})


def test_task_config_rejects_llm_enablement():
    with pytest.raises(TaskConfigError):
        load_task_config(None, {"allow_llm": True})
