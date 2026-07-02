import json
from pathlib import Path

from abqpilot.llm.config import load_llm_config, mask_secret


def test_llm_env_loads_when_present_and_masks_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "ABQPILOT_LLM_ENABLED=true",
                "ABQPILOT_LLM_PROVIDER=chatanywhere",
                "ABQPILOT_LLM_MODEL=deepseek-chat",
                "ABQPILOT_LLM_API_KEY=test-secret-value",
                "ABQPILOT_LLM_CHAT_URL=https://example.invalid/v1/chat/completions",
                "ABQPILOT_LLM_TIMEOUT_SECONDS=9",
            ]
        ),
        encoding="utf-8",
    )

    config = load_llm_config(env)

    assert config.env_found is True
    assert config.enabled is True
    assert config.provider == "chatanywhere"
    assert config.model == "deepseek-chat"
    assert config.api_key == "test-secret-value"
    masked = config.masked()
    assert masked["api_key"] == "tes****MASKED****"
    assert "secret-value" not in json.dumps(masked)


def test_missing_llm_env_does_not_fail(tmp_path):
    config = load_llm_config(tmp_path / ".env")

    assert config.env_found is False
    assert config.enabled is False
    assert config.masked()["api_key"] == "<not-configured>"


def test_legacy_openai_compatible_env_names_are_detected(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "ABQPILOT_LLM_ENABLED=true",
                "OPENAI_API_KEY=test-secret-value",
                "OPENAI_BASE_URL=https://api.chatanywhere.tech/v1",
                "EMBED_URL=https://api.chatanywhere.tech/v1/embeddings",
            ]
        ),
        encoding="utf-8",
    )

    config = load_llm_config(env)

    assert config.api_key == "test-secret-value"
    assert config.chat_url == "https://api.chatanywhere.tech/v1/chat/completions"
    assert config.embed_url == "https://api.chatanywhere.tech/v1/embeddings"


def test_mask_secret_never_returns_full_value():
    assert mask_secret("test-secret-value") == "tes****MASKED****"
    assert mask_secret(None) == "<not-configured>"


def test_env_is_gitignored_and_example_is_placeholder_only():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    example = Path(".env.example").read_text(encoding="utf-8")

    assert ".env" in gitignore
    assert "*.env" in gitignore
    assert ".env.*" in gitignore
    assert "!.env.example" in gitignore
    assert "sk-REPLACE_WITH_YOUR_KEY" in example
    assert "test-secret-value" not in example
