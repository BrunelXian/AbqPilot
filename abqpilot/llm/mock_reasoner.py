from __future__ import annotations

from typing import Any

from abqpilot.llm.schema import safe_reasoning_envelope, validate_reasoning_response


class MockReasoner:
    provider = "mock"
    model = "mock-reasoner"

    def reason(self, task_summary: dict[str, Any] | None = None, prompt: str | None = None) -> dict[str, Any]:
        task_summary = task_summary or {}
        if not task_summary:
            response = safe_reasoning_envelope(
                verdict="INSUFFICIENT_EVIDENCE",
                observation="Mock reasoner received no task summary.",
                diagnosis="There is not enough sanitized task state to recommend a workflow action.",
                recommended_next_action="Load a task workspace or pass sanitized task context.",
                provider=self.provider,
                model=self.model,
                risk_flags=["NO_TASK_SUMMARY"],
            )
        elif task_summary.get("pipeline", {}).get("failed_steps") or task_summary.get("failed_steps"):
            response = safe_reasoning_envelope(
                verdict="BLOCKED",
                observation="Mock reasoner found failed deterministic steps in the sanitized task summary.",
                diagnosis="A deterministic pipeline failure should be inspected before retrying.",
                recommended_next_action="Review failed step artifacts before retrying.",
                provider=self.provider,
                model=self.model,
                risk_flags=["FAILED_STEP_PRESENT"],
                confidence=0.8,
            )
        else:
            next_action = (
                task_summary.get("right_panel", {}).get("next_allowed_action")
                or "Continue with deterministic AbqPilot workflow gates."
            )
            response = safe_reasoning_envelope(
                verdict="OK",
                observation="Mock reasoner found no failed steps in the sanitized task summary.",
                diagnosis="The task appears safe to continue through existing deterministic gates.",
                recommended_next_action=next_action,
                provider=self.provider,
                model=self.model,
                allowed_actions=["refresh_status", "export_report", "run_mock_reasoner"],
                confidence=0.7,
            )
        response["validation"] = validate_reasoning_response(response)
        response["input_was_sanitized"] = True
        return response
