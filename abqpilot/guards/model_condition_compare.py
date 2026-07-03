from __future__ import annotations

from typing import Any

from abqpilot.guards.model_condition_schema import (
    MCP_FAIL_CONDITION_LOSS,
    MCP_FAIL_UNAUTHORIZED_CONDITION_CHANGE,
    MCP_PASS,
    MCP_REVIEW_REQUIRED,
)


BODY_HEAT_FLUX_CHECK = "MCPGuard.load_lifecycle.body_heat_flux_dflux_bf"
LOSS_CODE = "CONDITION_LOSS_LOAD_LIFECYCLE_DEACTIVATION_MISSING"


def compare_model_conditions(
    source_intent: dict[str, Any],
    source_exported: dict[str, Any],
    candidate: dict[str, Any],
    solver: dict[str, Any] | None,
    declared_target_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    target = _target_patch_isolation(source_exported, candidate, declared_target_changes)
    findings.extend(_load_lifecycle_findings(source_intent, candidate, "candidate"))
    if solver:
        findings.extend(_load_lifecycle_findings(source_intent, solver, "solver"))
    error_findings = [item for item in findings if item["severity"] == "error"]
    unknown_findings = [item for item in findings if item["status"] == "UNKNOWN"]
    if error_findings:
        status = MCP_FAIL_CONDITION_LOSS
    elif target["status"] == "FAIL":
        status = MCP_FAIL_UNAUTHORIZED_CONDITION_CHANGE
    elif unknown_findings or target["status"] == "REVIEW":
        status = MCP_REVIEW_REQUIRED
    else:
        status = MCP_PASS
    return {
        "guard_status": status,
        "eligible_for_solver": status == MCP_PASS,
        "condition_findings": findings,
        "target_patch_isolation": target,
    }


def _load_lifecycle_findings(source_intent: dict[str, Any], representation: dict[str, Any], role: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for load in source_intent.get("loads", []):
        if load.get("kind") != "BodyHeatFlux":
            continue
        for step in load.get("deactivated_steps", []):
            step_rep = _step(representation, step)
            if step_rep is None:
                findings.append(_finding(load, "UNKNOWN", "MCP_REVIEW_REQUIRED_STEP_NOT_FOUND", "warning", [], f"Review missing deactivation step `{step}` in {role} INP."))
                continue
            if step_rep.get("dflux", {}).get("has_dflux_op_new"):
                findings.append(
                    _finding(
                        load,
                        "PRESERVED",
                        "CONDITION_PRESERVED_LOAD_LIFECYCLE_DEACTIVATION_EXPLICIT",
                        "info",
                        step_rep.get("dflux", {}).get("keywords", []),
                        f"{role} INP explicitly resets DFLUX in `{step}`.",
                    )
                )
            else:
                findings.append(
                    _finding(
                        load,
                        "LOST",
                        LOSS_CODE,
                        "error",
                        [],
                        "Insert or preserve an explicit cooling-step DFLUX reset/removal representation before solver eligibility.",
                    )
                )
    if not findings:
        findings.append(
            {
                "category": "load_lifecycle",
                "subcategory": BODY_HEAT_FLUX_CHECK,
                "condition_name": None,
                "status": "UNKNOWN",
                "finding_code": "MCP_REVIEW_REQUIRED_NO_BODY_HEAT_FLUX_INTENT",
                "severity": "warning",
                "evidence_lines": [],
                "recommended_action": "Review source intent; no BodyHeatFlux lifecycle intent was extracted.",
            }
        )
    return findings


def _target_patch_isolation(source_exported: dict[str, Any], candidate: dict[str, Any], changes: list[dict[str, Any]]) -> dict[str, Any]:
    authorized: list[dict[str, Any]] = []
    unauthorized: list[dict[str, Any]] = []
    review: list[str] = []
    if not changes:
        return {"status": "REVIEW", "authorized_changes": [], "unauthorized_changes": [], "review_items": ["no declared target changes"]}
    for change in changes:
        if change.get("type") != "body_heat_flux_magnitude":
            review.append(f"unsupported target change type: {change.get('type')}")
            continue
        step_name = change.get("step")
        source_step = _step(source_exported, step_name)
        candidate_step = _step(candidate, step_name)
        source_values = _bf_values(source_step)
        candidate_values = _bf_values(candidate_step)
        expected_from = _num(change.get("from"))
        expected_to = _num(change.get("to"))
        if expected_from in source_values and expected_to in candidate_values:
            authorized.append({"type": change["type"], "step": step_name, "from": change.get("from"), "to": change.get("to")})
        else:
            unauthorized.append(
                {
                    "type": change.get("type"),
                    "step": step_name,
                    "source_values": source_values,
                    "candidate_values": candidate_values,
                    "expected_from": expected_from,
                    "expected_to": expected_to,
                }
            )
    status = "FAIL" if unauthorized else "REVIEW" if review else "PASS"
    return {"status": status, "authorized_changes": authorized, "unauthorized_changes": unauthorized, "review_items": review}


def _finding(load: dict[str, Any], status: str, code: str, severity: str, evidence: list[dict[str, Any]], action: str) -> dict[str, Any]:
    return {
        "category": "load_lifecycle",
        "subcategory": BODY_HEAT_FLUX_CHECK,
        "condition_name": load.get("name"),
        "status": status,
        "finding_code": code,
        "severity": severity,
        "evidence_lines": evidence,
        "recommended_action": action,
    }


def _step(payload: dict[str, Any] | None, name: str | None) -> dict[str, Any] | None:
    if not payload or not name:
        return None
    for step in payload.get("steps", []):
        if step.get("name") == name:
            return step
    return None


def _bf_values(step: dict[str, Any] | None) -> list[float]:
    if not step:
        return []
    values: list[float] = []
    for item in step.get("dflux", {}).get("positive_bf_lines", []) + step.get("dflux", {}).get("zero_bf_lines", []):
        if isinstance(item.get("value"), (int, float)):
            values.append(float(item["value"]))
    return values


def _num(value: Any) -> float | None:
    try:
        return float(str(value).replace("D", "E").replace("d", "e"))
    except (TypeError, ValueError):
        return None
