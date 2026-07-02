import json
from pathlib import Path

from abqpilot.patching.patch_application import apply_patch_proposal_preview


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "mvp1_am_thermal" / "base_heatflux_marker.inp"


def test_heat_flux_application_uses_candidate_copy_only(tmp_path):
    source = tmp_path / "source.inp"
    candidate = tmp_path / "candidate.inp"
    source.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
    before = source.read_text(encoding="utf-8")

    result = apply_patch_proposal_preview(_proposal(1.5), source, candidate)

    assert result["allowed"] is True
    assert candidate.exists()
    assert source.read_text(encoding="utf-8") == before
    assert result["builder_result"]["updated_magnitude"] == result["builder_result"]["original_magnitude"] * 1.5
    assert len(result["changed_lines"]) == 1


def test_unsupported_application_does_not_write_candidate(tmp_path):
    source = tmp_path / "source.inp"
    candidate = tmp_path / "candidate.inp"
    source.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
    proposal = _proposal(1.0)
    proposal["candidate_patch"]["patch_type"] = "output_request_adjustment"

    result = apply_patch_proposal_preview(proposal, source, candidate)

    assert result["allowed"] is False
    assert not candidate.exists()


def _proposal(scale):
    return {
        "candidate_patch": {
            "patch_type": "heat_flux_magnitude_adjustment",
            "value": scale,
        }
    }
