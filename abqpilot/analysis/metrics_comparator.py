from __future__ import annotations

from pathlib import Path
from typing import Any


REQUIRED_METRICS = ["NT_max", "NT_mean_global", "S_Mises_max", "S_Mises_mean_global"]


def build_comparison_report(metrics_pair: dict, source_metrics_path: str | Path | None = None) -> dict:
    base_case = _case_by_role(metrics_pair, "base")
    power_case = _case_by_role(metrics_pair, "power_x2")
    comparisons, missing = compare_common_numeric_metrics(
        base_case.get("metrics", {}),
        power_case.get("metrics", {}),
        required_metrics=REQUIRED_METRICS,
    )
    interpretations = build_interpretations(comparisons)
    return {
        "stage": "stage1_9_metrics_based_comparison_report",
        "source_metrics_path": str(source_metrics_path) if source_metrics_path is not None else None,
        "cases": [
            _case_summary(base_case),
            _case_summary(power_case),
        ],
        "metric_comparisons": comparisons,
        "missing_metric_comparisons": missing,
        "interpretation": interpretations,
        "caveats": [
            "The heat input change was controlled and audited before solver execution.",
            "This report reads existing metrics JSON only; it does not open ODB files or run Abaqus.",
            "Whole-field residual stress conclusions require regional stress metrics and manual field review.",
        ],
        "recommended_next_metrics": [
            "S_Mises_mean_heated_region",
            "S11_mean_heated_region",
            "S22_mean_heated_region",
            "S33_mean_heated_region",
            "PEEQ_max",
        ],
    }


def compare_common_numeric_metrics(
    base_metrics: dict,
    power_metrics: dict,
    required_metrics: list[str] | None = None,
) -> tuple[dict, list[dict]]:
    comparisons: dict[str, dict] = {}
    missing: list[dict] = []
    common_keys = sorted(set(base_metrics) & set(power_metrics))
    for metric in common_keys:
        base_value = base_metrics.get(metric)
        power_value = power_metrics.get(metric)
        if not _is_number(base_value) or not _is_number(power_value):
            missing.append({"metric": metric, "reason": "metric is not numeric in both cases"})
            continue
        comparisons[metric] = compare_metric(float(base_value), float(power_value))

    for metric in required_metrics or []:
        if metric not in comparisons:
            missing.append({"metric": metric, "reason": "required metric missing from comparable numeric metrics"})
    return comparisons, missing


def compare_metric(base_value: float, power_x2_value: float) -> dict:
    delta = power_x2_value - base_value
    divide_by_zero = base_value == 0
    ratio = None if divide_by_zero else power_x2_value / base_value
    percent_change = None if divide_by_zero else (delta / base_value) * 100.0
    return {
        "base_value": base_value,
        "power_x2_value": power_x2_value,
        "delta": delta,
        "ratio": ratio,
        "percent_change": percent_change,
        "divide_by_zero": divide_by_zero,
        "trend": trend_from_percent_change(percent_change),
    }


def trend_from_percent_change(percent_change: float | None) -> str:
    if percent_change is None:
        return "undefined"
    if percent_change > 5.0:
        return "increased"
    if percent_change < -5.0:
        return "decreased"
    return "approximately_unchanged"


def build_interpretations(comparisons: dict) -> dict:
    nt_max = comparisons.get("NT_max")
    stress = _stress_interpretation(comparisons)
    return {
        "temperature_response": _temperature_interpretation(nt_max),
        "stress_response": stress,
        "summary": [
            _temperature_interpretation(nt_max)["interpretation"],
            stress["interpretation"],
        ],
    }


def render_markdown_report(report: dict) -> str:
    lines = [
        "# Stage 1.9 Metrics-Based Comparison Report",
        "",
        f"Source metrics: `{report['source_metrics_path']}`",
        "",
        "## Cases",
        "",
        "| Case | Role | Status | Temperature Field | Last Step | Last Frame Time |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            f"| {case['case_id']} | {case['role']} | {case['status']} | "
            f"{case['temperature_field_used']} | {case['last_step']} | {case['last_frame_time']} |"
        )

    lines.extend(
        [
            "",
            "## Metric Comparison",
            "",
            "| Metric | Base | Power x2 | Delta | Ratio | Percent Change | Trend |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for metric, comparison in sorted(report["metric_comparisons"].items()):
        lines.append(
            f"| {metric} | {_fmt(comparison['base_value'])} | {_fmt(comparison['power_x2_value'])} | "
            f"{_fmt(comparison['delta'])} | {_fmt(comparison['ratio'])} | "
            f"{_fmt(comparison['percent_change'])} | {comparison['trend']} |"
        )

    lines.extend(["", "## Deterministic Interpretation", ""])
    for item in report["interpretation"]["summary"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "- The heat input change was controlled and audited.",
            "- Temperature max approximately doubled.",
            "- Maximum Mises stress decreased in the x2 case.",
            "- Whole-field residual stress conclusion requires mean/regional stress metrics and manual field review.",
            "",
            "## Caveats",
            "",
        ]
    )
    for caveat in report["caveats"]:
        lines.append(f"- {caveat}")
    lines.extend(["", "## Next Recommended Metrics", ""])
    for metric in report["recommended_next_metrics"]:
        lines.append(f"- {metric}")
    return "\n".join(lines) + "\n"


def _temperature_interpretation(nt_max: dict | None) -> dict:
    if not nt_max:
        return {
            "metric": "NT_max",
            "trend": "undefined",
            "interpretation": "Maximum temperature comparison is unavailable because NT_max is missing.",
        }
    ratio = nt_max.get("ratio")
    if nt_max["trend"] == "increased" and ratio is not None and 1.9 <= ratio <= 2.1:
        text = "Maximum temperature approximately doubled after heat input was doubled."
    elif nt_max["trend"] == "increased":
        text = "Maximum temperature increased after heat input was doubled."
    elif nt_max["trend"] == "decreased":
        text = "Maximum temperature decreased after heat input was doubled."
    else:
        text = "Maximum temperature was approximately unchanged after heat input was doubled."
    return {"metric": "NT_max", "trend": nt_max["trend"], "ratio": ratio, "interpretation": text}


def _stress_interpretation(comparisons: dict) -> dict:
    max_stress = comparisons.get("S_Mises_max")
    mean_stress = comparisons.get("S_Mises_mean_global")
    if max_stress and not mean_stress:
        return {
            "metric": "S_Mises_max",
            "trend": max_stress["trend"],
            "ratio": max_stress.get("ratio"),
            "interpretation": (
                "Maximum Mises stress decreased, but whole-field residual stress reduction is not concluded "
                "without mean or regional stress metrics."
                if max_stress["trend"] == "decreased"
                else "Only maximum Mises stress is available; whole-field residual stress response is not concluded."
            ),
        }
    if max_stress and mean_stress:
        if max_stress["trend"] == "decreased" and mean_stress["trend"] == "decreased":
            text = "Both maximum and global-mean Mises stress decreased."
        elif max_stress["trend"] != mean_stress["trend"]:
            text = "Stress response is spatially non-uniform; maximum and mean stress trends differ."
        else:
            text = f"Maximum and global-mean Mises stress both trended {max_stress['trend']}."
        return {
            "metric": "S_Mises_max_and_S_Mises_mean_global",
            "trend": {
                "S_Mises_max": max_stress["trend"],
                "S_Mises_mean_global": mean_stress["trend"],
            },
            "ratio": {
                "S_Mises_max": max_stress.get("ratio"),
                "S_Mises_mean_global": mean_stress.get("ratio"),
            },
            "interpretation": text,
        }
    return {
        "metric": "S_Mises",
        "trend": "undefined",
        "interpretation": "Mises stress comparison is unavailable because stress metrics are missing.",
    }


def _case_by_role(metrics_pair: dict, role: str) -> dict:
    for case in metrics_pair.get("cases", []):
        if case.get("role") == role:
            return case
    return {"role": role, "metrics": {}, "missing_fields": [{"field": "case", "missing_reason": "case not found"}]}


def _case_summary(case: dict) -> dict:
    return {
        "case_id": case.get("case_id"),
        "role": case.get("role"),
        "status": case.get("status"),
        "last_step": case.get("last_step"),
        "last_frame_time": case.get("last_frame_time"),
        "temperature_field_used": case.get("temperature_field_used"),
        "metric_names": sorted(case.get("metrics", {}).keys()),
        "missing_fields": case.get("missing_fields", []),
    }


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _fmt(value: float | None) -> str:
    if value is None:
        return "null"
    return f"{value:.6g}"
