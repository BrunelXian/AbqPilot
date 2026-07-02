from __future__ import annotations


def build_agent_observation(comparison_report: dict) -> dict:
    temperature = comparison_report["interpretation"]["temperature_response"]
    stress = comparison_report["interpretation"]["stress_response"]
    stress_metric = "S_Mises_max" if "S_Mises_max" in comparison_report["metric_comparisons"] else stress.get("metric")
    stress_comparison = comparison_report["metric_comparisons"].get("S_Mises_max", {})
    return {
        "task": "sanity_base_heat_input_x2_residual_stress_response",
        "input_change": {
            "type": "heat_input_magnitude_scale",
            "from": 1.0,
            "to": 2.0,
            "audited_diff": "only heat input magnitude changed",
        },
        "observations": {
            "temperature_response": {
                "metric": "NT_max",
                "trend": temperature.get("trend"),
                "ratio": _round_or_none(temperature.get("ratio")),
                "interpretation": temperature.get("interpretation"),
            },
            "stress_response": {
                "metric": stress_metric,
                "trend": stress_comparison.get("trend", _stress_trend(stress)),
                "ratio": _round_or_none(stress_comparison.get("ratio")),
                "interpretation": _stress_agent_text(stress),
            },
        },
        "recommended_next_action": "extract regional and mean stress metrics before making a stronger residual-stress conclusion",
        "allowed_next_actions": [
            "extract_additional_metrics",
            "manual_visual_review",
            "generate_report",
        ],
        "disallowed_next_actions": [
            "auto_repair",
            "submit_new_solver_job_without_approval",
            "llm_direct_model_edit",
        ],
    }


def _stress_agent_text(stress: dict) -> str:
    text = stress.get("interpretation", "")
    if text == "Both maximum and global-mean Mises stress decreased.":
        return (
            "Maximum and global-mean Mises residual stress decreased in the x2 heat case; "
            "regional stress metrics are still needed before making a stronger whole-field conclusion."
        )
    return text


def _stress_trend(stress: dict) -> str:
    trend = stress.get("trend")
    if isinstance(trend, dict):
        values = set(trend.values())
        return values.pop() if len(values) == 1 else "mixed"
    return trend


def _round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 3)
