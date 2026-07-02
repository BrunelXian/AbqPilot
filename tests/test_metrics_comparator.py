from abqpilot.analysis.metrics_comparator import (
    build_comparison_report,
    compare_metric,
    render_markdown_report,
    trend_from_percent_change,
)


def test_delta_ratio_percent_change_are_computed_correctly():
    comparison = compare_metric(10.0, 15.0)
    assert comparison["delta"] == 5.0
    assert comparison["ratio"] == 1.5
    assert comparison["percent_change"] == 50.0
    assert comparison["divide_by_zero"] is False


def test_divide_by_zero_is_handled_safely():
    comparison = compare_metric(0.0, 5.0)
    assert comparison["ratio"] is None
    assert comparison["percent_change"] is None
    assert comparison["divide_by_zero"] is True


def test_trends_work():
    assert trend_from_percent_change(6.0) == "increased"
    assert trend_from_percent_change(-6.0) == "decreased"
    assert trend_from_percent_change(5.0) == "approximately_unchanged"
    assert trend_from_percent_change(None) == "undefined"


def test_missing_optional_metrics_do_not_fail_report():
    report = build_comparison_report(_metrics_pair({"NT_max": 1.0}, {"NT_max": 2.0}))
    assert report["metric_comparisons"]["NT_max"]["ratio"] == 2.0
    assert report["missing_metric_comparisons"]


def test_stress_interpretation_does_not_overclaim_when_only_max_stress_is_present():
    report = build_comparison_report(_metrics_pair({"S_Mises_max": 100.0}, {"S_Mises_max": 80.0}))
    text = report["interpretation"]["stress_response"]["interpretation"]
    assert "whole-field residual stress reduction is not concluded" in text


def test_stress_interpretation_identifies_agreement_when_max_and_mean_decrease():
    report = build_comparison_report(
        _metrics_pair(
            {"S_Mises_max": 100.0, "S_Mises_mean_global": 50.0},
            {"S_Mises_max": 80.0, "S_Mises_mean_global": 40.0},
        )
    )
    assert report["interpretation"]["stress_response"]["interpretation"] == "Both maximum and global-mean Mises stress decreased."


def test_markdown_report_includes_whole_field_residual_stress_caveat():
    report = build_comparison_report(
        _metrics_pair(
            {"NT_max": 1.0, "S_Mises_max": 100.0, "S_Mises_mean_global": 50.0},
            {"NT_max": 2.0, "S_Mises_max": 80.0, "S_Mises_mean_global": 40.0},
        ),
        source_metrics_path="metrics.json",
    )
    markdown = render_markdown_report(report)
    assert "Whole-field residual stress conclusion requires mean/regional stress metrics" in markdown


def _metrics_pair(base_metrics: dict, power_metrics: dict) -> dict:
    return {
        "cases": [
            {
                "case_id": "base_power_1x",
                "role": "base",
                "status": "METRICS_EXTRACTED",
                "last_step": "Step_cool_00",
                "last_frame_time": 100.0,
                "temperature_field_used": "NT11",
                "metrics": base_metrics,
                "missing_fields": [],
            },
            {
                "case_id": "power_x2",
                "role": "power_x2",
                "status": "METRICS_EXTRACTED",
                "last_step": "Step_cool_00",
                "last_frame_time": 100.0,
                "temperature_field_used": "NT11",
                "metrics": power_metrics,
                "missing_fields": [],
            },
        ]
    }
