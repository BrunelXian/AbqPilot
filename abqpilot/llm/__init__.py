"""Optional runtime LLM provider contract for AbqPilot.

This package is not a Codex bridge and does not add autonomous repair.
"""

from abqpilot.llm.config import LlmConfig, load_llm_config
from abqpilot.llm.mock_reasoner import MockReasoner
from abqpilot.llm.provider import OpenAICompatibleProvider
from abqpilot.llm.schema import validate_reasoning_response

__all__ = [
    "LlmConfig",
    "MockReasoner",
    "OpenAICompatibleProvider",
    "load_llm_config",
    "validate_reasoning_response",
]
