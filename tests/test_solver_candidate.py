import json
from pathlib import Path

from abqpilot.solver.solver_candidate import validate_solver_candidate


def test_fixture_inp_rejected_as_solver_candidate(tmp_path):
    candidate = tmp_path / "fixture.inp"
    source = tmp_path / "source.inp"
    candidate.write_text("*Heading\n*Material, name=STEEL_FIXTURE\n", encoding="utf-8")
    source.write_text("source", encoding="utf-8")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "real_sanity_base_patch_candidate_summary.json").write_text(
        json.dumps({"fixture_reclassified_as_workflow_only": True, "real_sanity_base_source_used": False}),
        encoding="utf-8",
    )

    result = validate_solver_candidate(candidate, source, evidence, tmp_path / "run", "candidate_sanity_base_power_x2_stage4", 14)

    assert result["eligible"] is False
    assert result["verdict"] == "WARNING_ABQPILOT_SIMULATION_SOURCE_NOT_SANITY_BASE_DERIVED"


def test_sanity_base_candidate_accepted(tmp_path):
    candidate, source, evidence = _valid_candidate(tmp_path)

    result = validate_solver_candidate(candidate, source, evidence, tmp_path / "run", "candidate_sanity_base_power_x2_stage4", 14)

    assert result["eligible"] is True
    assert result["static_validator_status"] == "PASS"
    assert result["unrelated_changes_count"] == 0


def test_invalid_job_name_and_cpus_rejected(tmp_path):
    candidate, source, evidence = _valid_candidate(tmp_path)

    result = validate_solver_candidate(candidate, source, evidence, tmp_path / "run", "bad job; rm", 99)

    assert result["eligible"] is False
    assert "job_name_safe" in result["errors"]
    assert "cpus_valid" in result["errors"]


def _valid_candidate(tmp_path):
    from abqpilot.core.hash_utils import sha256_file
    from abqpilot.patching.real_sanity_base_candidate import CANDIDATE_HEAT_LINE, SOURCE_HEAT_LINE

    source = tmp_path / "source.inp"
    candidate = tmp_path / "candidate.inp"
    filler = "\n".join("** filler" for _ in range(12000))
    source.write_text(f"{SOURCE_HEAT_LINE}\n{filler}", encoding="utf-8")
    candidate.write_text(f"{CANDIDATE_HEAT_LINE}\n{filler}", encoding="utf-8")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "real_sanity_base_patch_candidate_summary.json").write_text(
        json.dumps(
            {
                "real_sanity_base_source_used": True,
                "candidate_inp_sha256": sha256_file(candidate),
                "source_inp_sha256": sha256_file(source),
                "exact_heat_flux_change": {"from": SOURCE_HEAT_LINE, "to": CANDIDATE_HEAT_LINE},
                "changed_lines_count": 1,
                "unrelated_changes_count": 0,
                "static_validator_status": "PASS",
                "diff_guard_status": "PASS",
                "physics_guard_status": "PASS",
            }
        ),
        encoding="utf-8",
    )
    (evidence / "patch_diff_report.json").write_text(json.dumps({"allowed": True, "changed_lines": [{}]}), encoding="utf-8")
    (evidence / "static_validation_report.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (evidence / "physics_guard_report.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    return candidate, source, evidence
