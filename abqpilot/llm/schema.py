from __future__ import annotations

from typing import Any


ALLOWED_VERDICTS = {
    "OK",
    "WAITING",
    "ACTION_RECOMMENDED",
    "BLOCKED",
    "INSUFFICIENT_EVIDENCE",
    "ERROR",
    "LLM_DISABLED",
    "PROVIDER_ERROR",
    "LLM_OUTPUT_REJECTED_BY_SAFETY_VALIDATOR",
}

FORBIDDEN_RECOMMENDATION_PHRASES = {
    "submit solver",
    "start queuerunner",
    "start queue runner",
    "launch queuerunner",
    "launch queue runner",
    "launch gui runner",
    "open odb directly",
    "edit inp directly",
    "enqueue without approval",
    "bypass guard",
    "bypass approval",
    "ignore approval token",
    "disable validator",
    "call abaqus",
    "run abaqus",
}


def validate_reasoning_response(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["response is not a JSON object"]}
    if payload.get("schema_version") != "0.1":
        errors.append("schema_version must be 0.1")
    if payload.get("verdict") not in ALLOWED_VERDICTS:
        errors.append("verdict is missing or unsupported")
    for key in ("provider", "model", "observation", "diagnosis", "recommended_next_action"):
        if not isinstance(payload.get(key), str):
            errors.append(f"{key} must be a string")
    for key in ("allowed_actions", "blocked_actions", "risk_flags"):
        if not isinstance(payload.get(key), list):
            errors.append(f"{key} must be a list")
    if payload.get("human_review_required") is not True:
        errors.append("human_review_required must be true")
    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("confidence must be a number between 0 and 1")
    forbidden = find_forbidden_recommendations(payload)
    if forbidden:
        errors.append("forbidden recommendations detected: " + ", ".join(forbidden))
    return {
        "valid": not errors,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "forbidden_recommendations": forbidden,
    }


def find_forbidden_recommendations(payload: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for key in ("observation", "diagnosis", "recommended_next_action"):
        value = payload.get(key)
        if isinstance(value, str):
            fields.append(value)
    for key in ("allowed_actions",):
        value = payload.get(key)
        if isinstance(value, list):
            fields.extend(str(item) for item in value)
    text = "\n".join(fields).lower()
    return sorted(phrase for phrase in FORBIDDEN_RECOMMENDATION_PHRASES if phrase in text)


def safe_reasoning_envelope(
    verdict: str,
    observation: str,
    recommended_next_action: str | None = None,
    provider: str = "mock",
    model: str = "mock-reasoner",
    diagnosis: str = "",
    allowed_actions: list[str] | None = None,
    blocked_actions: list[str] | None = None,
    risk_flags: list[str] | None = None,
    confidence: float = 0.0,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "provider": provider,
        "model": model,
        "verdict": verdict,
        "observation": observation,
        "diagnosis": diagnosis or observation,
        "recommended_next_action": recommended_next_action or "Continue with deterministic AbqPilot workflow gates.",
        "allowed_actions": allowed_actions or [],
        "blocked_actions": blocked_actions
        or [
            "submit_solver",
            "start_queue_runner",
            "open_odb_directly",
            "mutate_inp_directly",
            "bypass_approval_token",
        ],
        "risk_flags": risk_flags or [],
        "human_review_required": True,
        "confidence": float(confidence),
    }


def rejected_reasoning_envelope(
    payload: dict[str, Any],
    validation: dict[str, Any],
    provider: str,
    model: str,
) -> dict[str, Any]:
    result = safe_reasoning_envelope(
        verdict="LLM_OUTPUT_REJECTED_BY_SAFETY_VALIDATOR",
        observation="LLM output was rejected by AbqPilot's deterministic safety validator.",
        diagnosis="The provider response was missing required fields or recommended a forbidden action.",
        recommended_next_action="Ignore this LLM response and continue only through deterministic AbqPilot gates.",
        provider=provider,
        model=model,
        risk_flags=["LLM_OUTPUT_REJECTED"],
        confidence=0.0,
    )
    result["rejected_payload_keys"] = sorted(str(key) for key in payload.keys()) if isinstance(payload, dict) else []
    result["validation"] = validation
    return result
