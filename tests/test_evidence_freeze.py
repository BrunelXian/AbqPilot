from pathlib import Path

from abqpilot.analysis.evidence_freeze import (
    FINAL_VERDICT,
    build_demo_trace_summary,
    build_evidence_package,
    load_evidence,
    render_real_sanity_demo_report,
)


def test_demo_report_contains_required_evidence():
    root = Path(__file__).resolve().parents[1]
    summary = build_demo_trace_summary(load_evidence(root))
    report = render_real_sanity_demo_report(summary)
    assert "controlled heat-input x2 modification" in report
    assert "sanity_base_v01.cae" in report
    assert "*Dflux" in report
    assert "inst_plate.set-body-1, BF, 1e+10" in report
    assert "inst_plate.set-body-1, BF, 2e+10" in report
    assert "DiffGuard passed: True" in report
    assert "PhysicsGuard passed: True" in report
    assert "NT_max ratio: 2.0049356482188845" in report
    assert "Stronger residual-stress conclusion requires regional metrics" in report


def test_build_evidence_package_writes_required_outputs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    final = build_evidence_package(root, tmp_path)
    assert final["verdict"] == FINAL_VERDICT
    for name in [
        "evidence_manifest.json",
        "demo_trace_summary.json",
        "demo_trace_summary.md",
        "real_sanity_demo_report.md",
        "artifact_index.md",
        "final_verdict.json",
    ]:
        assert (tmp_path / name).exists()


def test_stage1_10_code_has_no_execution_or_odb_access_path():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "abqpilot" / "analysis" / "evidence_freeze.py",
        root / "examples" / "mvp1_am_thermal" / "run_stage1_10_evidence_freeze_real_sanity_demo.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = [
        "sub" + "process",
        "Po" + "pen",
        "os." + "system",
        "shell" + "=True",
        "open" + "Odb",
        "session." + "open" + "Odb",
        "submit" + "(",
        "wait" + "ForCompletion",
        "abq" + "jobpilot",
    ]
    assert not any(token in text for token in forbidden)
