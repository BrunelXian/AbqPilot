import json
from pathlib import Path

from abqpilot.solver.solver_report import intake_solver_run_output, report_solver_run


def test_intake_blocks_when_odb_missing(tmp_path):
    run = _run(tmp_path)

    result = intake_solver_run_output(run)

    assert result["verdict"] == "SOLVER_OUTPUT_NOT_READY"
    assert result["details"]["opened_odb"] is False


def test_report_uses_existing_gated_extractor(monkeypatch, tmp_path):
    run = _run(tmp_path)
    odb = run / "candidate_sanity_base_power_x2_stage4.odb"
    odb.write_text("odb", encoding="utf-8")
    (run / "candidate_sanity_base_power_x2_stage4.sta").write_text("THE ANALYSIS HAS COMPLETED", encoding="utf-8")
    intake_solver_run_output(run)
    runtime = tmp_path / "runtime.yaml"
    runtime.write_text(
        """runtime:
  abaqus_command: fake_abaqus
  allow_odb_read: true
  odb_read_mode: metrics_only
""",
        encoding="utf-8",
    )

    class FakeExtractor:
        def __init__(self, **kwargs):
            assert kwargs["allow_solver_submit"] is False
            assert kwargs["allow_abqjobpilot"] is False
            assert kwargs["allow_llm"] is False

        def prepare_request(self, contract_path, output_dir):
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            metrics = out / "odb_metrics_pair.json"
            metrics.write_text(
                json.dumps(
                    {
                        "cases": [
                            {"role": "base", "temperature_field_used": "NT11", "metrics": {"NT_max": 1.0, "S_Mises_max": 3.0}},
                            {"role": "power_x2", "temperature_field_used": "NT11", "metrics": {"NT_max": 2.1, "S_Mises_max": 2.0}},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            return {"output_dir": str(out), "metrics_json_path": str(metrics)}

        def extract(self, request):
            return {"verdict": "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY", "executed": True, "errors": []}

    monkeypatch.setattr("abqpilot.solver.solver_report.OdbMetricsExtractor", FakeExtractor)

    result = report_solver_run(run, runtime_config=runtime, baseline_odb=tmp_path / "base.odb")

    assert result["verdict"] == "CONTROLLED_SOLVER_MIXED_RESPONSE"
    assert result["details"]["opened_odb_only_via_gated_extractor"] is True
    assert result["details"]["queue_runner_launched"] is False


def _run(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "solver_preflight_result.json").write_text(
        json.dumps({"job_name": "candidate_sanity_base_power_x2_stage4"}),
        encoding="utf-8",
    )
    return run
