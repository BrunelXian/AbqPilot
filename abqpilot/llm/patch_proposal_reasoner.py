from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from abqpilot.llm.config import LlmConfig
from abqpilot.llm.patch_proposal_schema import (
    rejected_patch_proposal,
    safe_patch_proposal,
    validate_patch_proposal,
)
from abqpilot.llm.provider import _parse_provider_response, _safe_error


PATCH_SYSTEM_PROMPT = """You are AbqPilot's read-only patch proposal reviewer.
You receive a sanitized patch context only.
Return strict JSON only using the candidate patch proposal schema.
You cannot edit INP files, write CAE files, open ODB files, enqueue jobs, submit solvers, launch queue runners, or bypass validators.
Patch proposals are advisory only and always require human review plus StaticValidator, DiffGuard, and PhysicsGuard before any future application.
Return one top-level JSON object, not a wrapper object and not Markdown.
Use proposal_verdict only from NO_ACTION, PATCH_PROPOSED, HUMAN_REVIEW_ONLY, INSUFFICIENT_EVIDENCE.
Use candidate_patch.patch_type only from heat_flux_magnitude_adjustment, step_time_adjustment, output_request_adjustment, no_action, human_review_only.
Set candidate_patch.requires_human_review and every guard_requirements value to true."""


class MockPatchProposalReasoner:
    provider = "mock"
    model = "mock-patch-proposer"

    def propose(self, patch_context: dict[str, Any]) -> dict[str, Any]:
        repair_plan = patch_context.get("deterministic_repair_plan", {})
        evaluation = patch_context.get("evaluation", {})
        if not repair_plan and not evaluation:
            proposal = safe_patch_proposal(
                proposal_verdict="INSUFFICIENT_EVIDENCE",
                rationale="No deterministic evaluation or repair plan was available in the sanitized patch context.",
                patch_type="human_review_only",
                provider=self.provider,
                model=self.model,
                operation="review_missing_evidence",
                target="task_workspace",
                risk_flags=["MISSING_REPAIR_PLAN"],
                confidence=0.2,
            )
        elif repair_plan.get("repair_required") is False:
            proposal = safe_patch_proposal(
                proposal_verdict="NO_ACTION",
                rationale="The deterministic repair plan does not require a patch.",
                patch_type="no_action",
                provider=self.provider,
                model=self.model,
                operation="none",
                target="none",
                expected_effect="No patch is proposed. Continue monitoring or export the run report.",
                confidence=0.8,
            )
        elif "heat_flux_magnitude_adjustment" in repair_plan.get("allowed_patch_types", []):
            proposal = safe_patch_proposal(
                proposal_verdict="PATCH_PROPOSED",
                rationale="The deterministic repair plan allows heat flux magnitude adjustment for a future guarded patch stage.",
                patch_type="heat_flux_magnitude_adjustment",
                provider=self.provider,
                model=self.model,
                operation="propose_guarded_scale_review",
                target="heat_flux_magnitude",
                value=None,
                units=None,
                expected_effect="A future guarded builder may adjust heat flux magnitude after human review and validators pass.",
                risk_flags=["FUTURE_PATCH_REQUIRES_GUARDS"],
                confidence=0.55,
            )
        else:
            proposal = safe_patch_proposal(
                proposal_verdict="HUMAN_REVIEW_ONLY",
                rationale="The deterministic repair plan does not contain an allowed automatic proposal type for Stage 3.6.",
                patch_type="human_review_only",
                provider=self.provider,
                model=self.model,
                operation="human_review",
                target="repair_plan",
                risk_flags=["NO_ALLOWED_PATCH_TYPE_SELECTED"],
                confidence=0.4,
            )
        proposal["validation"] = validate_patch_proposal(proposal)
        return proposal


class OpenAICompatiblePatchProposalReasoner:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config

    def propose(self, patch_context: dict[str, Any]) -> dict[str, Any]:
        if not self.config.enabled:
            return self._error("Runtime LLM provider is disabled by configuration.")
        if not self.config.api_key or not self.config.chat_url:
            return self._error("provider is missing API key or chat URL")
        payload = {
            "instruction": (
                "Return strict JSON only with schema_version, provider, model, proposal_verdict, rationale, "
                "candidate_patch, guard_requirements, blocked_actions, risk_flags, confidence."
            ),
            "required_json_shape": {
                "schema_version": "0.1",
                "provider": self.config.provider,
                "model": self.config.model,
                "proposal_verdict": "NO_ACTION",
                "rationale": "brief rationale",
                "candidate_patch": {
                    "patch_type": "no_action",
                    "target": "none",
                    "operation": "none",
                    "value": None,
                    "units": None,
                    "expected_effect": "No patch is applied.",
                    "requires_human_review": True,
                },
                "guard_requirements": {
                    "requires_static_validator": True,
                    "requires_diff_guard": True,
                    "requires_physics_guard": True,
                    "requires_human_approval": True,
                },
                "blocked_actions": ["solver_submit", "queue_runner_launch", "direct_odb_open", "raw_inp_edit"],
                "risk_flags": [],
                "confidence": 0.5,
            },
            "allowed_patch_types": patch_context.get("allowed_patch_types", []),
            "forbidden_patch_types": patch_context.get("forbidden_patch_types", []),
            "patch_context": patch_context,
        }
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": PATCH_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, sort_keys=True)},
            ],
            "temperature": 0,
        }
        request = urllib.request.Request(
            self.config.chat_url or "",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + (self.config.api_key or ""),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            parsed = _parse_provider_response(raw)
        except (urllib.error.URLError, TimeoutError) as exc:
            return self._error(_safe_error(exc))
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return self._error("provider returned non-JSON or unsupported response shape")
        proposal = parsed if isinstance(parsed, dict) else {}
        proposal.setdefault("provider", self.config.provider)
        proposal.setdefault("model", self.config.model)
        validation = validate_patch_proposal(proposal)
        proposal["validation"] = validation
        if not validation.get("valid"):
            return rejected_patch_proposal(proposal, validation, self.config.provider, self.config.model)
        return proposal

    def _error(self, message: str) -> dict[str, Any]:
        proposal = safe_patch_proposal(
            proposal_verdict="INSUFFICIENT_EVIDENCE",
            rationale=message,
            patch_type="human_review_only",
            provider=self.config.provider,
            model=self.config.model,
            operation="provider_error_review",
            target="llm_provider",
            risk_flags=["PROVIDER_ERROR"],
            confidence=0.0,
        )
        proposal["validation"] = validate_patch_proposal(proposal)
        return proposal
