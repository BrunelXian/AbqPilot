from pathlib import Path

from abqpilot.patching.real_sanity_base_candidate import (
    CANDIDATE_HEAT_LINE,
    SOURCE_HEAT_LINE,
    classify_sources,
    create_real_sanity_base_patch_candidate,
    evaluate_power_2x_odb_equivalence,
)


def test_fixture_inp_is_not_production_solver_ready(tmp_path):
    fixture = tmp_path / "fixture.inp"
    fixture.write_text(
        """*Heading
*Material, name=STEEL_FIXTURE
*Node
1, 0., 0., 0.
*Element, type=DC3D8
1, 1
*Step
*Dflux
inst_plate.set-body-1, BF, 1e+10
*End Step
""",
        encoding="utf-8",
    )
    real_source = _write_realish_source(tmp_path / "real.inp")

    report = classify_sources(fixture_inp=fixture, source_inp=real_source, real_cae=tmp_path / "base.cae")

    assert report["fixture_inp"]["classification"] == "workflow_fixture_only"
    assert report["fixture_inp"]["solver_ready"] == "no"
    assert report["real_exported_inp"]["classification"] == "real_sanity_base_export"


def test_real_sanity_base_candidate_changes_only_heat_flux_line(tmp_path):
    source = _write_realish_source(tmp_path / "source.inp")
    source_before = source.read_text(encoding="utf-8")

    summary = create_real_sanity_base_patch_candidate(out_dir=tmp_path / "out", source_inp=source)
    candidate = Path(summary["candidate_inp_path"])

    assert summary["verdict"] == "PASS_ABQPILOT_V2_STAGE3_9B_REAL_SANITY_BASE_PATCH_CANDIDATE_READY"
    assert source.read_text(encoding="utf-8") == source_before
    assert SOURCE_HEAT_LINE in summary["exact_heat_flux_change"]["from"]
    assert CANDIDATE_HEAT_LINE in candidate.read_text(encoding="utf-8")
    assert summary["changed_lines_count"] == 1
    assert summary["unrelated_changes_count"] == 0
    assert summary["static_validator_status"] == "PASS"
    assert summary["diff_guard_status"] == "PASS"
    assert summary["physics_guard_status"] == "PASS"
    assert summary["solver_submitted"] is False
    assert summary["job_enqueued"] is False
    assert summary["opened_odb"] is False


def test_existing_power_2x_odb_equivalence_is_unproven_without_evidence(tmp_path, monkeypatch):
    candidate = _write_realish_source(tmp_path / "candidate.inp")
    candidate.write_text(candidate.read_text(encoding="utf-8").replace(SOURCE_HEAT_LINE, CANDIDATE_HEAT_LINE), encoding="utf-8")
    monkeypatch.setattr("abqpilot.patching.real_sanity_base_candidate.DEFAULT_POWER_2X_INP", tmp_path / "missing.inp")
    monkeypatch.setattr("abqpilot.patching.real_sanity_base_candidate.DEFAULT_POWER_2X_ODB", tmp_path / "missing.odb")
    monkeypatch.setattr("abqpilot.patching.real_sanity_base_candidate.DEFAULT_POWER_2X_LOG", tmp_path / "missing.log")

    evidence = evaluate_power_2x_odb_equivalence(candidate)

    assert evidence["status"] == "UNPROVEN"


def _write_realish_source(path: Path) -> Path:
    filler = "\n".join(f"** filler {idx}" for idx in range(50))
    text = f"""*Heading
real sanity-base derived source
{filler}
*Node
1, 0., 0., 0.
*Element, type=CPE4T
1, 1, 1, 1, 1
*Material, name="SS316L For AM"
*Elastic
1., 0.3
*Step, name=step_scan_00
*Coupled Temperature-displacement
0.05, 1.
*Dflux
{SOURCE_HEAT_LINE}
*Output, field
*Node Output
NT, RF, U
*Element Output, directions=YES
HFL, PEEQ, S
*End Step
"""
    path.write_text(text, encoding="utf-8")
    return path
