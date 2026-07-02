from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENV_KEYS = {
    "ABQPILOT_LLM_ENABLED",
    "ABQPILOT_LLM_PROVIDER",
    "ABQPILOT_LLM_MODEL",
    "ABQPILOT_LLM_API_KEY",
    "ABQPILOT_LLM_CHAT_URL",
    "ABQPILOT_LLM_EMBED_URL",
    "ABQPILOT_LLM_TIMEOUT_SECONDS",
    "ABQPILOT_LLM_MAX_INPUT_CHARS",
    "ABQPILOT_LLM_REQUIRE_JSON",
    "API_KEY",
    "API_URL",
    "EMBED_URL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
}


@dataclass(frozen=True)
class LlmConfig:
    enabled: bool = False
    provider: str = "mock"
    model: str = "mock-reasoner"
    api_key: str | None = None
    chat_url: str | None = None
    embed_url: str | None = None
    timeout_seconds: int = 30
    max_input_chars: int = 12000
    require_json: bool = True
    env_path: str | None = None
    env_found: bool = False

    def masked(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "api_key": mask_secret(self.api_key),
            "api_key_configured": bool(self.api_key),
            "chat_url": self.chat_url,
            "embed_url": self.embed_url,
            "timeout_seconds": self.timeout_seconds,
            "max_input_chars": self.max_input_chars,
            "require_json": self.require_json,
            "env_path": self.env_path,
            "env_found": self.env_found,
        }


def load_llm_config(env_path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> LlmConfig:
    target = Path(env_path) if env_path is not None else Path.cwd() / ".env"
    values = _read_env(target) if target.exists() else {}
    overrides = overrides or {}
    merged = {**values, **{key: value for key, value in overrides.items() if value is not None}}
    return LlmConfig(
        enabled=_as_bool(merged.get("ABQPILOT_LLM_ENABLED", merged.get("enabled", False))),
        provider=str(merged.get("ABQPILOT_LLM_PROVIDER", merged.get("provider", "mock"))),
        model=str(merged.get("ABQPILOT_LLM_MODEL", merged.get("model", "mock-reasoner"))),
        api_key=_first_present(merged, "ABQPILOT_LLM_API_KEY", "api_key", "API_KEY", "OPENAI_API_KEY"),
        chat_url=_chat_url(merged),
        embed_url=_first_present(merged, "ABQPILOT_LLM_EMBED_URL", "embed_url", "EMBED_URL"),
        timeout_seconds=_as_int(merged.get("ABQPILOT_LLM_TIMEOUT_SECONDS", merged.get("timeout_seconds", 30)), 30),
        max_input_chars=_as_int(merged.get("ABQPILOT_LLM_MAX_INPUT_CHARS", merged.get("max_input_chars", 12000)), 12000),
        require_json=_as_bool(merged.get("ABQPILOT_LLM_REQUIRE_JSON", merged.get("require_json", True))),
        env_path=str(target),
        env_found=target.exists(),
    )


def mask_secret(value: str | None) -> str:
    if not value:
        return "<not-configured>"
    prefix = value[:3] if len(value) >= 3 else ""
    return f"{prefix}****MASKED****"


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in ENV_KEYS:
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_present(values: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        text = _optional_str(values.get(key))
        if text:
            return text
    return None


def _chat_url(values: dict[str, Any]) -> str | None:
    explicit = _first_present(values, "ABQPILOT_LLM_CHAT_URL", "chat_url", "API_URL")
    if explicit:
        return explicit
    base = _first_present(values, "OPENAI_BASE_URL")
    if not base:
        return None
    base = base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"
