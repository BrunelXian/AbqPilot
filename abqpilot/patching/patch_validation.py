from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.llm.patch_proposal_schema import FORBIDDEN_PATCH_TYPES, validate_patch_proposal


APPLICABLE_VERDICT = "PATCH_PROPOSED"
NOT_APPLICABLE_VERDICTS = {"NO_ACTION", "HUMAN_REVIEW_ONLY", "INSUFFICIENT_EVIDENCE"}
SUPPORTED_PATCH_TYPES = {"heat_flux_magnitude_adjustment"}


def validate_patch_preview_request(proposal: dict[str, Any]) -> dict[str, Any]:
    validation = validate_patch_proposal(proposal)
    candidate = proposal.get("candidate_patch") if isinstance(proposal.get("candidate_patch"), dict) else {}
    patch_type = candidate.get("patch_type")
    proposal_verdict = proposal.get("proposal_verdict")
    errors: list[str] = []
    status = "PATCH_PREVIEW_READY_TO_APPLY"

    if not validation.get("valid"):
        return {
            "allowed": False,
            "status": "PATCH_PREVIEW_BLOCKED_NO_VALID_PROPOSAL",
            "errors": validation.get("errors", []),
            "proposal_validation": validation,
        }
    if proposal_verdict in NOT_APPLICABLE_VERDICTS:
        return {
            "allowed": False,
            "status": "PATCH_PREVIEW_NOT_APPLICABLE",
            "errors": [],
            "proposal_validation": validation,
        }
    if proposal_verdict != APPLICABLE_VERDICT:
        errors.append(f"unsupported proposal_verdict: {proposal_verdict}")
        status = "PATCH_PREVIEW_BLOCKED_NO_VALID_PROPOSAL"
    if patch_type in FORBIDDEN_PATCH_TYPES:
        errors.append(f"forbidden patch type: {patch_type}")
        status = "PATCH_PREVIEW_BLOCKED_FORBIDDEN_PATCH_TYPE"
    elif patch_type not in SUPPORTED_PATCH_TYPES:
        errors.append(f"unsupported patch type: {patch_type}")
        status = "PATCH_PREVIEW_BLOCKED_UNSUPPORTED_PATCH_TYPE"
    if patch_type == "heat_flux_magnitude_adjustment":
        value = candidate.get("value")
        if not isinstance(value, (int, float)) or float(value) <= 0:
            errors.append("heat_flux_magnitude_adjustment requires a positive numeric value scale")
            status = "PATCH_PREVIEW_BLOCKED_TARGET_NOT_IDENTIFIED"
    return {
        "allowed": not errors,
        "status": status if errors else "PATCH_PREVIEW_READY_TO_APPLY",
        "errors": errors,
        "proposal_validation": validation,
    }


def resolve_source_inp(task_dir: str | Path, source_inp: str | Path | None = None) -> Path | None:
    if source_inp is not None:
        path = Path(source_inp)
        return path if path.exists() else None
    task = Path(task_dir)
    artifacts_path = task / "artifacts.json"
    if not artifacts_path.exists():
        return None
    import json

    try:
        artifacts = json.loads(artifacts_path.read_text(encoding="utf-8")).get("artifacts", [])
    except json.JSONDecodeError:
        return None
    for name in ("base_heatflux_marker", "generated_power_x2", "candidate_inp"):
        for artifact in artifacts:
            if artifact.get("name") == name:
                path = Path(str(artifact.get("path", "")))
                if path.exists() and path.suffix.lower() == ".inp":
                    return path
    return None
