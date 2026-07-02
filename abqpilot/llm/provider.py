from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from abqpilot.llm.config import LlmConfig
from abqpilot.llm.schema import rejected_reasoning_envelope, safe_reasoning_envelope, validate_reasoning_response


SYSTEM_PROMPT = """You are AbqPilot's read-only engineering reasoning assistant.
You receive a sanitized task summary.
You must return strict JSON only.
You cannot execute tools, enqueue jobs, submit solvers, modify INP files, open ODB files, or bypass approval tokens.
You may only recommend safe next actions.
High-risk actions always require human review.
Set human_review_required to true in every response."""


class OpenAICompatibleProvider:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config

    def available(self) -> dict[str, Any]:
        return {
            "available": bool(self.config.enabled and self.config.api_key and self.config.chat_url),
            "config": self.config.masked(),
        }

    def reason(self, task_summary: dict[str, Any]) -> dict[str, Any]:
        if not self.config.enabled:
            return self._disabled()
        if not self.config.api_key or not self.config.chat_url:
            return self._provider_error("provider is missing API key or chat URL")
        prompt = {
            "instruction": (
                "Return strict JSON only with schema_version, provider, model, verdict, observation, diagnosis, "
                "recommended_next_action, allowed_actions, blocked_actions, risk_flags, human_review_required, confidence."
            ),
            "allowed_verdicts": ["OK", "WAITING", "ACTION_RECOMMENDED", "BLOCKED", "INSUFFICIENT_EVIDENCE", "ERROR"],
            "forbidden_recommendations": [
                "submit solver",
                "start external queue runner",
                "open ODB directly",
                "edit INP directly",
                "enqueue without approval",
                "bypass guard",
                "ignore approval token",
                "disable validator",
            ],
            "task_summary": task_summary,
        }
        return self._chat(prompt)

    def probe(self) -> dict[str, Any]:
        if not self.config.enabled:
            return self._disabled()
        if not self.config.api_key or not self.config.chat_url:
            return self._provider_error("provider is missing API key or chat URL")
        return self._chat({"test": "Return JSON {\"ok\": true}."}, probe=True)

    def _chat(self, payload: dict[str, Any], probe: bool = False) -> dict[str, Any]:
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, sort_keys=True)},
            ],
            "temperature": 0,
        }
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.config.chat_url or "",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + (self.config.api_key or ""),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            return self._provider_error(_safe_error(exc))
        try:
            parsed = _parse_provider_response(raw)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            return self._provider_error("provider returned non-JSON or unsupported response shape")
        if probe:
            return {
                "schema_version": "0.1",
                "provider": self.config.provider,
                "model": self.config.model,
                "verdict": "PASS" if parsed.get("ok") is True else "REVIEW_RECOMMENDED",
                "summary": "LLM provider probe completed.",
                "recommendations": [],
                "safety": _safety(),
                "probe_response": parsed,
                "validation": {"valid": True, "errors": []},
            }
        result = parsed if isinstance(parsed, dict) else {}
        if "schema_version" not in result:
            result = safe_reasoning_envelope(
                verdict="ERROR",
                observation="Provider response was not in the AbqPilot reasoning schema.",
                diagnosis="The response could not be parsed as strict Stage 3.5B reasoning JSON.",
                recommended_next_action="Use mock provider or inspect provider JSON behavior.",
                provider=self.config.provider,
                model=self.config.model,
                risk_flags=["PROVIDER_SCHEMA_MISMATCH"],
            )
        result.setdefault("provider", self.config.provider)
        result.setdefault("model", self.config.model)
        validation = validate_reasoning_response(result)
        result["validation"] = validation
        if not validation.get("valid"):
            return rejected_reasoning_envelope(result, validation, self.config.provider, self.config.model)
        return result

    def _disabled(self) -> dict[str, Any]:
        result = safe_reasoning_envelope(
            verdict="LLM_DISABLED",
            observation="Runtime LLM provider is disabled by configuration.",
            diagnosis="ABQPILOT_LLM_ENABLED is false or not configured for runtime provider use.",
            recommended_next_action="Use --provider mock or enable the provider explicitly in .env.",
            provider=self.config.provider,
            model=self.config.model,
            risk_flags=["LLM_DISABLED"],
        )
        result["validation"] = validate_reasoning_response(result)
        return result

    def _provider_error(self, message: str) -> dict[str, Any]:
        result = safe_reasoning_envelope(
            verdict="PROVIDER_ERROR",
            observation=message,
            diagnosis="The configured provider could not complete the request.",
            recommended_next_action="Check masked provider configuration and network availability.",
            provider=self.config.provider,
            model=self.config.model,
            risk_flags=["PROVIDER_ERROR"],
        )
        result["validation"] = validate_reasoning_response(result)
        return result


def _parse_provider_response(raw: str) -> dict[str, Any]:
    payload = json.loads(raw)
    content = payload.get("choices", [{}])[0].get("message", {}).get("content")
    if isinstance(content, str):
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        return json.loads(content)
    return payload


def _safety() -> dict[str, bool]:
    return {
        "sent_full_inp": False,
        "sent_odb": False,
        "submitted_solver": False,
        "mutated_inputs": False,
    }


def _safe_error(exc: BaseException) -> str:
    text = str(exc)
    if "Bearer " in text:
        return "provider request failed"
    return text
