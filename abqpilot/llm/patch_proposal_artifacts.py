from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_patch_proposal_artifacts(
    task_dir: str | Path,
    patch_context: dict[str, Any],
    proposal: dict[str, Any],
    request_metadata: dict[str, Any],
) -> dict[str, str]:
    artifact_dir = Path(task_dir) / "llm_patch_proposals"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "llm_patch_context": artifact_dir / "llm_patch_context.json",
        "llm_patch_request_metadata": artifact_dir / "llm_patch_request_metadata.json",
        "llm_patch_raw_response": artifact_dir / "llm_patch_raw_response.json",
        "llm_candidate_patch_proposal": artifact_dir / "llm_candidate_patch_proposal.json",
        "llm_patch_safety_validation": artifact_dir / "llm_patch_safety_validation.json",
        "llm_candidate_patch_proposal_md": artifact_dir / "llm_candidate_patch_proposal.md",
    }
    _write_json(paths["llm_patch_context"], patch_context)
    _write_json(paths["llm_patch_request_metadata"], _sanitize_metadata(request_metadata))
    _write_json(paths["llm_patch_raw_response"], _safe_raw_response(proposal))
    _write_json(paths["llm_candidate_patch_proposal"], proposal)
    _write_json(paths["llm_patch_safety_validation"], proposal.get("validation", {"valid": False, "errors": ["missing validation"]}))
    paths["llm_candidate_patch_proposal_md"].write_text(_markdown(proposal), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()} | {"artifact_dir": str(artifact_dir)}


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    clean = dict(metadata)
    for key in ("api_key", "authorization", "Authorization", "headers"):
        clean.pop(key, None)
    clean["authorization_header_written"] = False
    return clean


def _safe_raw_response(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": proposal.get("provider"),
        "model": proposal.get("model"),
        "proposal_verdict": proposal.get("proposal_verdict"),
        "rationale": proposal.get("rationale"),
        "candidate_patch": proposal.get("candidate_patch"),
        "guard_requirements": proposal.get("guard_requirements"),
        "blocked_actions": proposal.get("blocked_actions", []),
        "risk_flags": proposal.get("risk_flags", []),
        "confidence": proposal.get("confidence"),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _markdown(proposal: dict[str, Any]) -> str:
    candidate = proposal.get("candidate_patch", {})
    validation = proposal.get("validation", {})
    risks = proposal.get("risk_flags", [])
    return "\n".join(
        [
            "# LLM Candidate Patch Proposal",
            "",
            f"Provider: {proposal.get('provider')}",
            f"Model: {proposal.get('model')}",
            f"Proposal verdict: {proposal.get('proposal_verdict')}",
            f"Safety validator: {validation.get('status', 'UNKNOWN')}",
            "",
            "## Candidate Patch",
            f"- Type: {candidate.get('patch_type')}",
            f"- Target: {candidate.get('target')}",
            f"- Operation: {candidate.get('operation')}",
            f"- Value: {candidate.get('value')}",
            f"- Units: {candidate.get('units')}",
            f"- Requires human review: {candidate.get('requires_human_review')}",
            "",
            "## Rationale",
            str(proposal.get("rationale", "")),
            "",
            "## Expected Effect",
            str(candidate.get("expected_effect", "")),
            "",
            "## Risk Flags",
            "\n".join(f"- {item}" for item in risks) if risks else "None",
            "",
            "## Safety Boundary",
            "This proposal is advisory only. Stage 3.6 does not mutate INP files, submit solvers, enqueue jobs, launch external queue workers, or open ODB files.",
            "",
        ]
    )
