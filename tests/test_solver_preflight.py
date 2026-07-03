import json
from pathlib import Path

from abqpilot.solver.solver_preflight import build_solver_command_preview, prepare_solver_run


def test_prepare_solver_run_writes_sanitized_command_preview(tmp_path):
    candidate, source, evidence = _valid_candidate(tmp_path)

    result = prepare_solver_run(candidate, source, evidence, cpus=14, run_root=tmp_path / "runs", abaqus_command="D:\\ABAQUS2024\\Commands\\abq2024.bat")

    assert result["verdict"] == "SOLVER_RUN_PREPARED"
    run_dir = result["details"]["solver_run_dir"]
    preview = json.loads((Path(run_dir) / "solver_command_preview.json").read_text())
    assert preview["command"] == [
        "D:\\ABAQUS2024\\Commands\\abq2024.bat",
        "job=candidate_sanity_base_power_x2_stage4",
        "input=candidate_sanity_base_power_x2_stage4.inp",
        "cpus=14",
        "interactive",
    ]


def test_command_preview_rejects_bad_cpus():
    try:
        build_solver_command_preview("abq.bat", "candidate_sanity_base_power_x2_stage4", "candidate_sanity_base_power_x2_stage4.inp", 15)
    except ValueError as exc:
        assert "cpus" in str(exc)
    else:
        raise AssertionError("expected ValueError")


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
