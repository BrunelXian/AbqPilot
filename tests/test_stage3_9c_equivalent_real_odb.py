import json
from pathlib import Path

from abqpilot.patching.equivalent_real_odb_stage import (
    _build_report,
    run_stage3_9c_equivalent_odb,
    verify_stage3_9c_preconditions,
)
from abqpilot.patching.real_sanity_base_candidate import CANDIDATE_HEAT_LINE, SOURCE_HEAT_LINE


def test_equivalent_odb_intake_requires_stage3_9b_equivalence_yes(tmp_path):
    stage = _stage3_9b_dir(tmp_path, equivalence="UNPROVEN")
    odb = tmp_path / "power2x.odb"
    odb.write_text("odb placeholder", encoding="utf-8")

    preconditions = verify_stage3_9c_preconditions(stage, odb)

    assert preconditions["ok"] is False
    assert preconditions["checks"]["equivalence_yes"] is False


def test_missing_odb_blocks_safely(tmp_path):
    stage = _stage3_9b_dir(tmp_path)
    missing = tmp_path / "missing.odb"

    preconditions = verify_stage3_9c_preconditions(stage, missing)

    assert preconditions["ok"] is False
    assert preconditions["checks"]["equivalent_odb_exists"] is False


def test_locked_odb_blocks_safely(tmp_path):
    stage = _stage3_9b_dir(tmp_path)
    odb = tmp_path / "power2x.odb"
    odb.write_text("odb placeholder", encoding="utf-8")
    odb.with_suffix(".lck").write_text("locked", encoding="utf-8")

    preconditions = verify_stage3_9c_preconditions(stage, odb)

    assert preconditions["ok"] is False
    assert preconditions["checks"]["equivalent_odb_unlocked"] is False


def test_stage3_9c_uses_gated_extractor_and_records_traceability(monkeypatch, tmp_path):
    stage = _stage3_9b_dir(tmp_path)
    odb = tmp_path / "power2x.odb"
    ref = tmp_path / "power1x.odb"
    odb.write_text("odb placeholder", encoding="utf-8")
    ref.write_text("odb placeholder", encoding="utf-8")
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
            output = Path(output_dir)
            output.mkdir(parents=True, exist_ok=True)
            metrics = output / "odb_metrics_pair.json"
            metrics.write_text(
                json.dumps(
                    {
                        "cases": [
                            {"role": "base", "temperature_field_used": "NT11", "metrics": {"NT_max": 100.0, "S_Mises_max": 10.0}},
                            {"role": "power_x2", "temperature_field_used": "NT11", "metrics": {"NT_max": 210.0, "S_Mises_max": 8.0}},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            return {"output_dir": str(output), "metrics_json_path": str(metrics), "verdict": "ODB_METRICS_REQUEST_PREPARED"}

        def extract(self, request):
            return {
                "verdict": "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY",
                "executed": True,
                "errors": [],
            }

    monkeypatch.setattr("abqpilot.patching.equivalent_real_odb_stage.OdbMetricsExtractor", FakeExtractor)

    result = run_stage3_9c_equivalent_odb(stage, tmp_path / "out", odb, ref, runtime)

    assert result["success"] is True
    assert result["details"]["evaluation_verdict"] == "EQUIVALENT_PATCHED_MIXED"
    report = json.loads((tmp_path / "out" / "equivalent_odb_report.json").read_text(encoding="utf-8"))
    assert report["candidate_traceability"] == "sanity-base-derived"
    assert report["submitted_solver"] is False
    assert report["created_new_queue_job"] is False
    assert report["opened_odb_directly"] is False


def test_report_handles_mixed_metrics_without_overclaiming(tmp_path):
    report = _build_report(
        tmp_path,
        {"candidate_inp_path": "candidate.inp"},
        {"accepted_odb_path": "patched.odb"},
        {"opened_odb_only_via_gated_extractor": True},
        {
            "cases": [
                {"role": "base", "temperature_field_used": "NT11", "metrics": {"NT_max": 254.0, "S_Mises_max": 461.0}},
                {"role": "power_x2", "temperature_field_used": "NT11", "metrics": {"NT_max": 510.0, "S_Mises_max": 377.0}},
            ]
        },
    )

    assert report["evaluation_verdict"] == "EQUIVALENT_PATCHED_MIXED"


def _stage3_9b_dir(tmp_path, equivalence="YES"):
    stage = tmp_path / "stage3_9b"
    stage.mkdir()
    source = stage / "source_sanity_base_export.inp"
    candidate = stage / "candidate_sanity_base_power_x2.inp"
    source.write_text(SOURCE_HEAT_LINE + "\n", encoding="utf-8")
    candidate.write_text(CANDIDATE_HEAT_LINE + "\n", encoding="utf-8")
    (stage / "real_sanity_base_patch_candidate_summary.json").write_text(
        json.dumps(
            {
                "source_inp_path": str(source),
                "candidate_inp_path": str(candidate),
                "candidate_inp_sha256": _sha256(candidate),
                "changed_lines_count": 1,
                "unrelated_changes_count": 0,
                "static_validator_status": "PASS",
                "diff_guard_status": "PASS",
                "physics_guard_status": "PASS",
                "existing_power_2x_odb_equivalent_candidate_output": equivalence,
            }
        ),
        encoding="utf-8",
    )
    (stage / "patch_diff_report.json").write_text(json.dumps({"allowed": True, "changed_lines": [{"line_index": 0}]}), encoding="utf-8")
    (stage / "static_validation_report.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (stage / "physics_guard_report.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    return stage


def _sha256(path):
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
