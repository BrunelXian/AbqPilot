from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_reasoning_artifacts(
    task_dir: str | Path,
    input_summary: dict[str, Any],
    reasoning: dict[str, Any],
    request_metadata: dict[str, Any],
) -> dict[str, str]:
    artifact_dir = Path(task_dir) / "llm_reasoning"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "llm_input_summary": artifact_dir / "llm_input_summary.json",
        "llm_request_metadata": artifact_dir / "llm_request_metadata.json",
        "llm_reasoning_raw_response": artifact_dir / "llm_reasoning_raw_response.json",
        "llm_reasoning_result": artifact_dir / "llm_reasoning_result.json",
        "llm_reasoning_result_md": artifact_dir / "llm_reasoning_result.md",
        "llm_safety_validation": artifact_dir / "llm_safety_validation.json",
    }
    safe_metadata = _sanitize_metadata(request_metadata)
    _write_json(paths["llm_input_summary"], input_summary)
    _write_json(paths["llm_request_metadata"], safe_metadata)
    _write_json(paths["llm_reasoning_raw_response"], _safe_raw_response(reasoning))
    _write_json(paths["llm_reasoning_result"], reasoning)
    _write_json(paths["llm_safety_validation"], reasoning.get("validation", {"valid": False, "errors": ["missing validation"]}))
    paths["llm_reasoning_result_md"].write_text(_markdown(reasoning), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()} | {"artifact_dir": str(artifact_dir)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    clean = dict(metadata)
    clean.pop("api_key", None)
    clean.pop("authorization", None)
    clean.pop("Authorization", None)
    clean["authorization_header_written"] = False
    return clean


def _safe_raw_response(reasoning: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": reasoning.get("provider"),
        "model": reasoning.get("model"),
        "verdict": reasoning.get("verdict"),
        "observation": reasoning.get("observation"),
        "diagnosis": reasoning.get("diagnosis"),
        "recommended_next_action": reasoning.get("recommended_next_action"),
        "allowed_actions": reasoning.get("allowed_actions", []),
        "blocked_actions": reasoning.get("blocked_actions", []),
        "risk_flags": reasoning.get("risk_flags", []),
        "human_review_required": reasoning.get("human_review_required"),
        "confidence": reasoning.get("confidence"),
    }


def _markdown(reasoning: dict[str, Any]) -> str:
    validation = reasoning.get("validation", {})
    risks = reasoning.get("risk_flags", [])
    return "\n".join(
        [
            "# AbqPilot LLM Reasoning",
            "",
            f"Provider: {reasoning.get('provider')}",
            f"Model: {reasoning.get('model')}",
            f"Verdict: {reasoning.get('verdict')}",
            f"Safety validator: {validation.get('status', 'UNKNOWN')}",
            "",
            "## Observation",
            str(reasoning.get("observation", "")),
            "",
            "## Diagnosis",
            str(reasoning.get("diagnosis", "")),
            "",
            "## Recommended Next Action",
            str(reasoning.get("recommended_next_action", "")),
            "",
            "## Risk Flags",
            "\n".join(f"- {item}" for item in risks) if risks else "None",
            "",
            "## Safety Boundary",
            "The LLM is read-only and advisory. It cannot execute tools, enqueue jobs, submit solvers, modify INP files, or open ODB files.",
            "",
        ]
    )
