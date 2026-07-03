import json
from pathlib import Path

from abqpilot.patching.patched_job_metrics import extract_patched_job_metrics


def test_metrics_extraction_blocks_without_accepted_output(tmp_path):
    workflow = _workflow(tmp_path, accepted=False)

    result = extract_patched_job_metrics(workflow)

    assert result["verdict"] == "PATCHED_JOB_METRICS_BLOCKED_NO_ACCEPTED_OUTPUT"
    assert result["details"]["submitted_solver"] is False
    assert result["details"]["opened_odb_directly"] is False


def test_metrics_extraction_uses_existing_gated_extractor(monkeypatch, tmp_path):
    workflow = _workflow(tmp_path, accepted=True)
    calls = {"prepare": 0, "extract": 0}

    class FakeExtractor:
        def __init__(self, **kwargs):
            assert kwargs["allow_solver_submit"] is False
            assert kwargs["allow_abqjobpilot"] is False
            assert kwargs["allow_llm"] is False

        def prepare_request(self, contract_path, output_dir):
            calls["prepare"] += 1
            output = Path(output_dir)
            output.mkdir(parents=True, exist_ok=True)
            metrics = output / "odb_metrics_pair.json"
            metrics.write_text(json.dumps({"cases": [{"role": "power_x2", "metrics": {"NT_max": 1.0}}]}), encoding="utf-8")
            return {"output_dir": str(output), "metrics_json_path": str(metrics), "verdict": "ODB_METRICS_REQUEST_PREPARED"}

        def extract(self, request):
            calls["extract"] += 1
            return {
                "verdict": "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY",
                "executed": True,
                "errors": [],
                "warnings": [],
            }

    monkeypatch.setattr("abqpilot.patching.patched_job_metrics.OdbMetricsExtractor", FakeExtractor)

    result = extract_patched_job_metrics(workflow)

    assert result["verdict"] == "PATCHED_JOB_METRICS_READY"
    assert calls == {"prepare": 1, "extract": 1}
    assert result["details"]["opened_odb_only_via_gated_extractor"] is True


def _workflow(tmp_path, accepted):
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    odb = tmp_path / "patched.odb"
    if accepted:
        odb.write_text("fixture", encoding="utf-8")
    (workflow / "patched_job_output_intake_result.json").write_text(
        json.dumps(
            {
                "job_id": "q_patch",
                "output_accepted": accepted,
                "accepted_odb_path": str(odb) if accepted else None,
            }
        ),
        encoding="utf-8",
    )
    return workflow
