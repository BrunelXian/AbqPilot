import json
from pathlib import Path

from abqpilot import cli
from abqpilot.analysis.evaluation import evaluate_metrics
from abqpilot.analysis.repair_plan import build_repair_plan, write_repair_plan


def test_evaluation_returns_insufficient_metrics_when_missing():
    evaluation = evaluate_metrics(metrics={}, comparison_report={})

    assert evaluation["evaluation_verdict"] == "INSUFFICIENT_METRICS"
    assert evaluation["opened_odb"] is False
    assert evaluation["submitted_solver"] is False


def test_evaluation_confirms_thermal_response_and_notes_stress_relaxation():
    evaluation = evaluate_metrics(metrics=_metrics(), comparison_report=_comparison())

    assert evaluation["evaluation_verdict"] == "PASS"
    assert "PASS_THERMAL_RESPONSE_CONFIRMED" in evaluation["observations"]
    assert "OBSERVED_STRESS_RELAXATION_OR_NON_MONOTONIC_RESPONSE" in evaluation["observations"]


def test_repair_plan_forbids_high_risk_patch_types_and_does_not_mutate_inp():
    plan = build_repair_plan({"evaluation_verdict": "INSUFFICIENT_METRICS"}, task_id="task")

    assert plan["repair_required"] is True
    assert "material_change" in plan["forbidden_patch_types"]
    assert "geometry_change" in plan["forbidden_patch_types"]
    assert "mesh_change" in plan["forbidden_patch_types"]
    assert "solver_submit" in plan["forbidden_patch_types"]
    assert plan["mutated_inp"] is False
    assert plan["submitted_solver"] is False


def test_write_repair_plan_creates_json_and_markdown(tmp_path):
    paths = write_repair_plan(tmp_path, {"evaluation_verdict": "PASS", "task_id": "task"})

    assert Path(paths["evaluation_json"]).exists()
    assert Path(paths["repair_plan_json"]).exists()
    assert Path(paths["repair_plan_md"]).exists()
    assert "No solver job was submitted" in Path(paths["repair_plan_md"]).read_text(encoding="utf-8")


def test_generate_repair_plan_cli_records_task_artifacts(tmp_path):
    task_dir = tmp_path / "runs" / "tasks" / "task"
    task_dir.mkdir(parents=True)
    metrics_path = tmp_path / "metrics.json"
    comparison_path = tmp_path / "comparison.json"
    metrics_path.write_text(json.dumps(_metrics()), encoding="utf-8")
    comparison_path.write_text(json.dumps(_comparison()), encoding="utf-8")
    (task_dir / "artifacts.json").write_text(
        json.dumps(
            {
                "task_id": "task",
                "artifacts": [
                    {"name": "odb_metrics_json", "path": str(metrics_path), "kind": "generated", "exists": True},
                    {"name": "comparison_report_json", "path": str(comparison_path), "kind": "generated", "exists": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = cli.command_generate_repair_plan(task_dir=task_dir)

    assert result["verdict"] == "PASS"
    artifacts = json.loads((task_dir / "artifacts.json").read_text(encoding="utf-8"))
    assert any(item["name"] == "evaluation_json" for item in artifacts["artifacts"])
    assert any(item["name"] == "repair_plan_json" for item in artifacts["artifacts"])


def _metrics():
    return {
        "cases": [
            {"role": "base", "status": "METRICS_EXTRACTED", "metrics": {"NT_max": 100.0, "S_Mises_max": 200.0}},
            {"role": "power_x2", "status": "METRICS_EXTRACTED", "metrics": {"NT_max": 200.0, "S_Mises_max": 160.0}},
        ]
    }


def _comparison():
    return {
        "source_metrics_path": "metrics.json",
        "metric_comparisons": {
            "NT_max": {"ratio": 2.0, "trend": "increased"},
            "S_Mises_max": {"ratio": 0.8, "trend": "decreased"},
        },
        "missing_metric_comparisons": [],
    }
