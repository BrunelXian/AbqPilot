from pathlib import Path

from abqpilot.analysis.agent_observation_builder import build_agent_observation
from abqpilot.analysis.metrics_comparator import build_comparison_report


def test_agent_observation_includes_audited_input_change():
    observation = build_agent_observation(_comparison_report())
    assert observation["input_change"] == {
        "type": "heat_input_magnitude_scale",
        "from": 1.0,
        "to": 2.0,
        "audited_diff": "only heat input magnitude changed",
    }


def test_agent_observation_disallows_auto_repair_and_direct_model_edit():
    observation = build_agent_observation(_comparison_report())
    assert "auto_repair" in observation["disallowed_next_actions"]
    assert "llm_direct_model_edit" in observation["disallowed_next_actions"]


def test_stage1_9_code_has_no_execution_path():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "abqpilot" / "analysis" / "metrics_comparator.py",
        root / "abqpilot" / "analysis" / "agent_observation_builder.py",
        root / "examples" / "mvp1_am_thermal" / "run_stage1_9_metrics_based_comparison_report.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = [
        "sub" + "process",
        "Po" + "pen",
        "os." + "system",
        "shell" + "=True",
        "open" + "Odb",
        "session." + "open" + "Odb",
        "submit" + "(",
        "wait" + "ForCompletion",
        "abq" + "jobpilot",
    ]
    assert not any(token in text for token in forbidden)


def _comparison_report() -> dict:
    metrics_pair = {
        "cases": [
            {
                "case_id": "base_power_1x",
                "role": "base",
                "status": "METRICS_EXTRACTED",
                "last_step": "Step_cool_00",
                "last_frame_time": 100.0,
                "temperature_field_used": "NT11",
                "metrics": {"NT_max": 100.0, "S_Mises_max": 100.0, "S_Mises_mean_global": 50.0},
                "missing_fields": [],
            },
            {
                "case_id": "power_x2",
                "role": "power_x2",
                "status": "METRICS_EXTRACTED",
                "last_step": "Step_cool_00",
                "last_frame_time": 100.0,
                "temperature_field_used": "NT11",
                "metrics": {"NT_max": 200.0, "S_Mises_max": 80.0, "S_Mises_mean_global": 40.0},
                "missing_fields": [],
            },
        ]
    }
    return build_comparison_report(metrics_pair)
