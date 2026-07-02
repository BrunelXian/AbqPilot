from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def evaluate_metrics(
    metrics: dict[str, Any] | None = None,
    comparison_report: dict[str, Any] | None = None,
    task_id: str | None = None,
    source_metrics: str | Path | None = None,
) -> dict[str, Any]:
    metrics = metrics or {}
    comparison_report = comparison_report or {}
    comparisons = comparison_report.get("metric_comparisons", {})
    missing = list(comparison_report.get("missing_metric_comparisons", []))
    observations: list[str] = []
    errors: list[str] = []

    if not metrics and not comparisons:
        verdict = "INSUFFICIENT_METRICS"
        errors.append("metrics and comparison report are missing")
    elif not comparisons:
        verdict = "INSUFFICIENT_METRICS"
        errors.append("metric comparison data is missing")
    else:
        nt_max = comparisons.get("NT_max")
        if not nt_max or nt_max.get("ratio") is None:
            verdict = "INSUFFICIENT_METRICS"
            errors.append("NT_max comparison is missing")
        elif 1.8 <= float(nt_max["ratio"]) <= 2.2 and nt_max.get("trend") == "increased":
            verdict = "PASS"
            observations.append("PASS_THERMAL_RESPONSE_CONFIRMED")
        else:
            verdict = "REPAIR_RECOMMENDED"
            observations.append("THERMAL_RESPONSE_OUTSIDE_EXPECTED_RANGE")

    stress = comparisons.get("S_Mises_max")
    if stress and stress.get("trend") in {"decreased", "approximately_unchanged"}:
        observations.append("OBSERVED_STRESS_RELAXATION_OR_NON_MONOTONIC_RESPONSE")
    if any(item.get("metric") == "NT_max" for item in missing):
        verdict = "INSUFFICIENT_METRICS"
    if any(case.get("status") in {"FAILED", "EXTRACTION_FAILED"} for case in metrics.get("cases", [])):
        verdict = "FAIL_STOP"
        errors.append("one or more metric extraction cases failed")

    return {
        "schema_version": "0.1",
        "task_id": task_id,
        "source_metrics": str(source_metrics) if source_metrics is not None else comparison_report.get("source_metrics_path"),
        "evaluation_verdict": verdict,
        "observations": observations,
        "missing_metric_comparisons": missing,
        "errors": errors,
        "opened_odb": False,
        "submitted_solver": False,
    }


def write_evaluation(path: str | Path, evaluation: dict[str, Any]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evaluation, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(target)
