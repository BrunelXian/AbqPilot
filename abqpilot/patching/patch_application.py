from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder


def apply_patch_proposal_preview(
    proposal: dict[str, Any],
    source_inp: str | Path,
    candidate_inp: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    candidate = proposal.get("candidate_patch", {})
    patch_type = candidate.get("patch_type")
    if patch_type != "heat_flux_magnitude_adjustment":
        return {
            "status": "PATCH_PREVIEW_BLOCKED_UNSUPPORTED_PATCH_TYPE",
            "allowed": False,
            "errors": [f"unsupported patch type: {patch_type}"],
            "changed_lines": [],
        }
    scale = float(candidate.get("value"))
    request = {
        "builder": "HeatFluxPatchBuilder",
        "patch_type": patch_type,
        "source_inp_path": str(source_inp),
        "base_inp_path": str(source_inp),
        "candidate_inp_path": str(candidate_inp),
        "generated_inp_path": str(candidate_inp),
        "parameters": {"heat_flux_scale": scale},
        "dry_run": bool(dry_run),
    }
    if dry_run:
        return {
            "status": "PATCH_PREVIEW_DRY_RUN_READY",
            "allowed": True,
            "request": request,
            "changed_lines": [],
            "errors": [],
        }
    build_status = HeatFluxPatchBuilder().build(request)
    status = "PATCH_PREVIEW_APPLICATION_READY" if build_status.get("allowed") else "PATCH_PREVIEW_BLOCKED_TARGET_NOT_IDENTIFIED"
    return {
        "status": status,
        "allowed": bool(build_status.get("allowed")),
        "request": request,
        "builder_result": build_status,
        "changed_lines": build_status.get("changes", []),
        "errors": build_status.get("errors", []),
    }
