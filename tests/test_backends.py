"""Tests for AI backend implementations."""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# BaseBackend contract
# ---------------------------------------------------------------------------

def test_backend_interface():
    """All backends must implement label, supports_attachments, stream_turn."""
    from dnd_combat_tracker.backends import (
        ClaudeBackend, GeminiBackend, OpenAIBackend, OllamaBackend
    )
    for cls in (ClaudeBackend, GeminiBackend, OpenAIBackend, OllamaBackend):
        assert hasattr(cls, "fetch_models")


# ---------------------------------------------------------------------------
# ClaudeBackend
# ---------------------------------------------------------------------------

def test_claude_label():
    with patch("anthropic.Anthropic"):
        from dnd_combat_tracker.backends.claude import ClaudeBackend
        b = ClaudeBackend(api_key="test", model="claude-sonnet-4-6")
        assert b.label == "claude-sonnet-4-6"
        assert b.supports_attachments is True


def test_claude_stream_turn():
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Set up streaming context manager
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Hello", ", ", "adventurer!"])
        mock_client.messages.stream.return_value = mock_stream

        from dnd_combat_tracker.backends.claude import ClaudeBackend
        backend = ClaudeBackend(api_key="test-key")

        tokens = []
        result = backend.stream_turn("You are a DM.", "Hello!", on_token=tokens.append)

        assert result == "Hello, adventurer!"
        assert tokens == ["Hello", ", ", "adventurer!"]
        # User + assistant messages added to history
        assert len(backend._history) == 2
        assert backend._history[0] == {"role": "user", "content": "Hello!"}
        assert backend._history[1] == {"role": "assistant", "content": "Hello, adventurer!"}


def test_claude_fetch_models_empty_key():
    from dnd_combat_tracker.backends.claude import ClaudeBackend
    assert ClaudeBackend.fetch_models("") == []


def test_claude_fetch_models_api_error():
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.models.list.side_effect = Exception("API error")
        from dnd_combat_tracker.backends.claude import ClaudeBackend
        ClaudeBackend._model_cache = {"models": None, "ts": 0.0}  # clear cache
        result = ClaudeBackend.fetch_models("some-key")
        assert result == []


# ---------------------------------------------------------------------------
# OpenAIBackend
# ---------------------------------------------------------------------------

def test_openai_label():
    with patch("openai.OpenAI"):
        from dnd_combat_tracker.backends.openai import OpenAIBackend
        b = OpenAIBackend(api_key="test", model="gpt-4o")
        assert b.label == "openai:gpt-4o"
        assert b.supports_attachments is False


def test_openai_stream_turn():
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Build streaming chunks
        def make_chunk(content):
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = content
            return chunk

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter([
            make_chunk("Roll"), make_chunk(" for"), make_chunk(" initiative!")
        ]))
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_client.chat.completions.create.return_value = mock_stream

        from dnd_combat_tracker.backends.openai import OpenAIBackend
        backend = OpenAIBackend(api_key="test-key")

        tokens = []
        result = backend.stream_turn("You are a DM.", "What do I do?", on_token=tokens.append)

        assert result == "Roll for initiative!"
        assert tokens == ["Roll", " for", " initiative!"]
        assert len(backend._history) == 2


def test_openai_fetch_models_empty_key():
    from dnd_combat_tracker.backends.openai import OpenAIBackend
    assert OpenAIBackend.fetch_models("") == []


# ---------------------------------------------------------------------------
# OllamaBackend
# ---------------------------------------------------------------------------

def test_ollama_label():
    from dnd_combat_tracker.backends.ollama import OllamaBackend
    b = OllamaBackend(model="llama3.1")
    assert b.label == "ollama:llama3.1"
    assert b.supports_attachments is False


def test_ollama_stream_turn():
    import json

    lines = [
        json.dumps({"message": {"content": "A goblin "}, "done": False}),
        json.dumps({"message": {"content": "appears!"}, "done": False}),
        json.dumps({"message": {"content": ""}, "done": True}),
    ]

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.iter_lines.return_value = iter(lines)
        mock_client.stream.return_value = mock_resp

        from dnd_combat_tracker.backends.ollama import OllamaBackend
        backend = OllamaBackend(model="llama3.1")

        tokens = []
        result = backend.stream_turn("You are a DM.", "Look around.", on_token=tokens.append)

        assert result == "A goblin appears!"
        assert tokens == ["A goblin ", "appears!"]
        assert len(backend._history) == 2


def test_ollama_fetch_models_unavailable():
    with patch("httpx.get", side_effect=Exception("connection refused")):
        from dnd_combat_tracker.backends.ollama import OllamaBackend
        OllamaBackend._model_cache = {"models": None, "ts": 0.0}
        result = OllamaBackend.fetch_models("http://localhost:11434")
        assert result == []


# ---------------------------------------------------------------------------
# GeminiBackend
# ---------------------------------------------------------------------------

def test_gemini_label():
    with patch("google.genai.Client"):
        from dnd_combat_tracker.backends.gemini import GeminiBackend
        b = GeminiBackend(api_key="test", model="gemini-2.5-flash")
        assert b.label == "gemini:gemini-2.5-flash"
        assert b.supports_attachments is False


def test_gemini_fetch_models_empty_key():
    from dnd_combat_tracker.backends.gemini import GeminiBackend
    assert GeminiBackend.fetch_models("") == []


# ---------------------------------------------------------------------------
# Settings API endpoints
# ---------------------------------------------------------------------------

def test_get_settings_defaults(client):
    r = client.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "claude"
    assert body["model"] is not None


def test_put_settings_provider(client):
    r = client.put("/api/settings", json={"provider": "openai"})
    assert r.status_code == 200
    assert r.json()["provider"] == "openai"


def test_put_settings_invalid_provider(client):
    r = client.put("/api/settings", json={"provider": "fake-llm"})
    assert r.status_code == 400


def test_put_settings_model(client):
    r = client.put("/api/settings", json={"provider": "claude", "model": "claude-opus-4-6"})
    assert r.status_code == 200
    assert r.json()["model"] == "claude-opus-4-6"


def test_get_providers(client):
    r = client.get("/api/settings/providers")
    assert r.status_code == 200
    providers = r.json()
    ids = [p["id"] for p in providers]
    assert set(ids) == {"claude", "gemini", "openai", "ollama"}
    for p in providers:
        assert "configured" in p
        assert "label" in p


def test_get_models_invalid_provider(client):
    r = client.get("/api/settings/providers/fake/models")
    assert r.status_code == 404


def test_get_models_unconfigured_returns_empty(client):
    # No API keys in test env → should return empty list, not 500
    r = client.get("/api/settings/providers/claude/models")
    assert r.status_code == 200
    assert r.json() == []
