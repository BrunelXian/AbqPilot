from __future__ import annotations

from typing import Any


ALLOWED_PATCH_TYPES = {
    "heat_flux_magnitude_adjustment",
    "step_time_adjustment",
    "output_request_adjustment",
    "no_action",
    "human_review_only",
}

FORBIDDEN_PATCH_TYPES = {
    "material_change",
    "elastic_property_change",
    "plastic_property_change",
    "geometry_change",
    "mesh_change",
    "boundary_condition_change",
    "contact_change",
    "solver_submit",
    "queue_runner_launch",
    "direct_odb_open",
    "raw_inp_edit",
}

ALLOWED_PROPOSAL_VERDICTS = {
    "NO_ACTION",
    "PATCH_PROPOSED",
    "HUMAN_REVIEW_ONLY",
    "INSUFFICIENT_EVIDENCE",
    "REJECTED_BY_SAFETY_VALIDATOR",
}

FORBIDDEN_TEXT_PHRASES = {
    "submit solver",
    "run solver",
    "call abaqus",
    "start queuerunner",
    "start queue runner",
    "launch queuerunner",
    "launch queue runner",
    "open odb",
    "edit inp",
    "raw inp",
    "bypass validator",
    "bypass guard",
    "bypass approval",
    "change material",
    "change geometry",
    "change mesh",
    "modify mesh",
}


def validate_patch_proposal(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "status": "FAIL", "errors": ["proposal is not a JSON object"], "forbidden_terms": []}
    if payload.get("schema_version") != "0.1":
        errors.append("schema_version must be 0.1")
    if not isinstance(payload.get("provider"), str):
        errors.append("provider must be a string")
    if not isinstance(payload.get("model"), str):
        errors.append("model must be a string")
    if payload.get("proposal_verdict") not in ALLOWED_PROPOSAL_VERDICTS:
        errors.append("proposal_verdict is missing or unsupported")
    if not isinstance(payload.get("rationale"), str):
        errors.append("rationale must be a string")
    candidate = payload.get("candidate_patch")
    if not isinstance(candidate, dict):
        errors.append("candidate_patch must be an object")
        candidate = {}
    patch_type = candidate.get("patch_type")
    if patch_type not in ALLOWED_PATCH_TYPES:
        errors.append(f"candidate_patch.patch_type is not allowed: {patch_type}")
    if patch_type in FORBIDDEN_PATCH_TYPES:
        errors.append(f"candidate_patch.patch_type is forbidden: {patch_type}")
    if candidate.get("requires_human_review") is not True:
        errors.append("candidate_patch.requires_human_review must be true")
    if not isinstance(candidate.get("operation"), str):
        errors.append("candidate_patch.operation must be a string")
    guard_requirements = payload.get("guard_requirements")
    if not isinstance(guard_requirements, dict):
        errors.append("guard_requirements must be an object")
        guard_requirements = {}
    for key in (
        "requires_static_validator",
        "requires_diff_guard",
        "requires_physics_guard",
        "requires_human_approval",
    ):
        if guard_requirements.get(key) is not True:
            errors.append(f"guard_requirements.{key} must be true")
    for key in ("blocked_actions", "risk_flags"):
        if not isinstance(payload.get(key), list):
            errors.append(f"{key} must be a list")
    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("confidence must be a number between 0 and 1")
    forbidden_terms = _find_forbidden_terms(payload)
    if forbidden_terms:
        errors.append("forbidden terms detected: " + ", ".join(forbidden_terms))
    return {
        "valid": not errors,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "forbidden_terms": forbidden_terms,
    }


def safe_patch_proposal(
    proposal_verdict: str,
    rationale: str,
    patch_type: str,
    provider: str = "mock",
    model: str = "mock-patch-proposer",
    operation: str = "none",
    target: str = "none",
    value: Any = None,
    units: str | None = None,
    expected_effect: str = "No automatic simulation mutation is performed.",
    risk_flags: list[str] | None = None,
    confidence: float = 0.0,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "provider": provider,
        "model": model,
        "proposal_verdict": proposal_verdict,
        "rationale": rationale,
        "candidate_patch": {
            "patch_type": patch_type,
            "target": target,
            "operation": operation,
            "value": value,
            "units": units,
            "expected_effect": expected_effect,
            "requires_human_review": True,
        },
        "guard_requirements": {
            "requires_static_validator": True,
            "requires_diff_guard": True,
            "requires_physics_guard": True,
            "requires_human_approval": True,
        },
        "blocked_actions": [
            "direct_inp_mutation",
            "solver_submit",
            "queue_runner_launch",
            "direct_odb_open",
            "guard_bypass",
        ],
        "risk_flags": risk_flags or [],
        "confidence": float(confidence),
    }


def rejected_patch_proposal(payload: dict[str, Any], validation: dict[str, Any], provider: str, model: str) -> dict[str, Any]:
    result = safe_patch_proposal(
        proposal_verdict="REJECTED_BY_SAFETY_VALIDATOR",
        rationale="LLM patch proposal was rejected by AbqPilot's deterministic safety validator.",
        patch_type="human_review_only",
        provider=provider,
        model=model,
        operation="review_rejected_provider_output",
        target="llm_patch_proposal",
        expected_effect="No patch is applied. Human review is required.",
        risk_flags=["LLM_PATCH_PROPOSAL_REJECTED"],
        confidence=0.0,
    )
    result["status"] = "LLM_PATCH_PROPOSAL_REJECTED_BY_SAFETY_VALIDATOR"
    result["rejected_payload_keys"] = sorted(str(key) for key in payload.keys()) if isinstance(payload, dict) else []
    result["validation"] = validation
    return result


def _find_forbidden_terms(payload: dict[str, Any]) -> list[str]:
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), dict) else {}
    values = [
        payload.get("rationale", ""),
        candidate.get("patch_type", ""),
        candidate.get("target", ""),
        candidate.get("operation", ""),
        candidate.get("expected_effect", ""),
    ]
    text = "\n".join(str(value).lower() for value in values)
    terms = set(term for term in FORBIDDEN_TEXT_PHRASES if term in text)
    terms.update(term for term in FORBIDDEN_PATCH_TYPES if term in text)
    return sorted(terms)
