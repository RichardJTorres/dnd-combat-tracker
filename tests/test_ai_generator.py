"""Tests for AI monster generation — factory and generator logic."""

import json
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# get_backend factory
# ---------------------------------------------------------------------------

def _make_session(provider="claude", model=None):
    """Build a fake DB session that returns provider/model from settings."""
    from dnd_combat_tracker.db import settings as settings_db

    def fake_get(session, key, default=None):
        if key == "provider":
            return provider
        if key == f"{provider}_model":
            return model or {"claude": "claude-sonnet-4-6", "gemini": "gemini-2.5-flash",
                             "openai": "gpt-4o", "ollama": "llama3.1"}[provider]
        return default

    session = MagicMock()
    return session, fake_get


def test_get_backend_claude(monkeypatch):
    session, fake_get = _make_session("claude")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.anthropic_api_key", "sk-test")

    with patch("anthropic.Anthropic"):
        from dnd_combat_tracker.backends import get_backend, ClaudeBackend
        backend = get_backend(session)
    assert isinstance(backend, ClaudeBackend)


def test_get_backend_openai(monkeypatch):
    session, fake_get = _make_session("openai")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.openai_api_key", "sk-test")

    with patch("openai.OpenAI"):
        from dnd_combat_tracker.backends import get_backend, OpenAIBackend
        backend = get_backend(session)
    assert isinstance(backend, OpenAIBackend)


def test_get_backend_gemini(monkeypatch):
    session, fake_get = _make_session("gemini")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.gemini_api_key", "gm-test")

    with patch("google.genai.Client"):
        from dnd_combat_tracker.backends import get_backend, GeminiBackend
        backend = get_backend(session)
    assert isinstance(backend, GeminiBackend)


def test_get_backend_ollama(monkeypatch):
    session, fake_get = _make_session("ollama")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.ollama_host", "http://localhost:11434")

    from dnd_combat_tracker.backends import get_backend, OllamaBackend
    backend = get_backend(session)
    assert isinstance(backend, OllamaBackend)


def test_get_backend_missing_claude_key_raises(monkeypatch):
    session, fake_get = _make_session("claude")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.anthropic_api_key", "")

    from dnd_combat_tracker.backends import get_backend
    with pytest.raises(ValueError, match="Anthropic API key"):
        get_backend(session)


def test_get_backend_missing_openai_key_raises(monkeypatch):
    session, fake_get = _make_session("openai")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.openai_api_key", "")

    from dnd_combat_tracker.backends import get_backend
    with pytest.raises(ValueError, match="OpenAI API key"):
        get_backend(session)


def test_get_backend_missing_gemini_key_raises(monkeypatch):
    session, fake_get = _make_session("gemini")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)
    monkeypatch.setattr("dnd_combat_tracker.backends.settings.gemini_api_key", "")

    from dnd_combat_tracker.backends import get_backend
    with pytest.raises(ValueError, match="Gemini API key"):
        get_backend(session)


def test_get_backend_unknown_provider_raises(monkeypatch):
    session, fake_get = _make_session("unknown-llm")
    monkeypatch.setattr("dnd_combat_tracker.backends.settings_db.get", fake_get)

    from dnd_combat_tracker.backends import get_backend
    with pytest.raises(ValueError, match="Unknown provider"):
        get_backend(session)


# ---------------------------------------------------------------------------
# generate_monster — helpers
# ---------------------------------------------------------------------------

def _mock_backend(response: str) -> MagicMock:
    """Create a mock BaseBackend whose stream_turn returns response."""
    backend = MagicMock()
    backend.stream_turn.return_value = response
    return backend


MINIMAL_MONSTER = {
    "name": "Test Goblin",
    "size": "Small",
    "creature_type": "humanoid",
    "cr": 0.25,
    "hp": 7,
    "hp_formula": "2d6",
    "ac": 15,
    "ac_notes": "leather armor",
    "speed": "30 ft.",
    "strength": 8,
    "dexterity": 14,
    "constitution": 10,
    "intelligence": 10,
    "wisdom": 8,
    "charisma": 8,
    "traits": json.dumps([{"name": "Nimble Escape", "description": "Disengage as bonus action."}]),
    "actions": json.dumps([{"name": "Scimitar", "description": "+4 to hit, 1d6+2 slashing."}]),
    "source": "AI Generated",
}


# ---------------------------------------------------------------------------
# generate_monster — happy path
# ---------------------------------------------------------------------------

def test_generate_monster_plain_json():
    from dnd_combat_tracker.ai_generator import generate_monster
    backend = _mock_backend(json.dumps(MINIMAL_MONSTER))
    result = generate_monster(backend, "a small goblin")
    assert result["name"] == "Test Goblin"
    assert result["cr"] == 0.25
    assert result["source"] == "AI Generated"


def test_generate_monster_calls_stream_turn_once():
    from dnd_combat_tracker.ai_generator import generate_monster, SYSTEM_PROMPT
    backend = _mock_backend(json.dumps(MINIMAL_MONSTER))
    generate_monster(backend, "a fire goblin")
    backend.stream_turn.assert_called_once()
    call_args = backend.stream_turn.call_args
    assert call_args[0][0] == SYSTEM_PROMPT
    assert "fire goblin" in call_args[0][1]


def test_generate_monster_strips_json_fence():
    from dnd_combat_tracker.ai_generator import generate_monster
    raw = f"```json\n{json.dumps(MINIMAL_MONSTER)}\n```"
    backend = _mock_backend(raw)
    result = generate_monster(backend, "a goblin")
    assert result["name"] == "Test Goblin"


def test_generate_monster_strips_plain_fence():
    from dnd_combat_tracker.ai_generator import generate_monster
    raw = f"```\n{json.dumps(MINIMAL_MONSTER)}\n```"
    backend = _mock_backend(raw)
    result = generate_monster(backend, "a goblin")
    assert result["name"] == "Test Goblin"


def test_generate_monster_source_forced_to_ai_generated():
    from dnd_combat_tracker.ai_generator import generate_monster
    monster = {**MINIMAL_MONSTER, "source": "Monster Manual"}
    backend = _mock_backend(json.dumps(monster))
    result = generate_monster(backend, "a goblin")
    assert result["source"] == "AI Generated"


# ---------------------------------------------------------------------------
# generate_monster — field coercion (LLM returns nested objects/arrays)
# ---------------------------------------------------------------------------

def test_generate_monster_coerces_nested_traits():
    """LLM returns traits as a real array instead of a JSON string."""
    from dnd_combat_tracker.ai_generator import generate_monster
    monster = {
        **MINIMAL_MONSTER,
        "traits": [{"name": "Nimble Escape", "description": "Disengage as bonus action."}],
    }
    backend = _mock_backend(json.dumps(monster))
    result = generate_monster(backend, "a goblin")
    # Must be a string (JSON-encoded)
    assert isinstance(result["traits"], str)
    parsed = json.loads(result["traits"])
    assert parsed[0]["name"] == "Nimble Escape"


def test_generate_monster_coerces_nested_actions():
    from dnd_combat_tracker.ai_generator import generate_monster
    monster = {
        **MINIMAL_MONSTER,
        "actions": [{"name": "Scimitar", "description": "+4 to hit."}],
    }
    backend = _mock_backend(json.dumps(monster))
    result = generate_monster(backend, "a goblin")
    assert isinstance(result["actions"], str)


def test_generate_monster_coerces_nested_saving_throws():
    from dnd_combat_tracker.ai_generator import generate_monster
    monster = {**MINIMAL_MONSTER, "saving_throws": {"dex": 4, "wis": 2}}
    backend = _mock_backend(json.dumps(monster))
    result = generate_monster(backend, "a goblin")
    assert isinstance(result["saving_throws"], str)
    assert json.loads(result["saving_throws"]) == {"dex": 4, "wis": 2}


def test_generate_monster_empty_list_becomes_none():
    from dnd_combat_tracker.ai_generator import generate_monster
    monster = {**MINIMAL_MONSTER, "legendary_actions": []}
    backend = _mock_backend(json.dumps(monster))
    result = generate_monster(backend, "a goblin")
    assert result.get("legendary_actions") is None


def test_generate_monster_empty_string_becomes_none():
    from dnd_combat_tracker.ai_generator import generate_monster
    monster = {**MINIMAL_MONSTER, "damage_immunities": ""}
    backend = _mock_backend(json.dumps(monster))
    result = generate_monster(backend, "a goblin")
    assert result.get("damage_immunities") is None


# ---------------------------------------------------------------------------
# generate_monster — error cases
# ---------------------------------------------------------------------------

def test_generate_monster_non_json_raises():
    from dnd_combat_tracker.ai_generator import generate_monster, MonsterGenerationError
    backend = _mock_backend("Sorry, I cannot create that monster.")
    with pytest.raises(MonsterGenerationError, match="non-JSON"):
        generate_monster(backend, "a goblin")


def test_generate_monster_json_array_raises():
    from dnd_combat_tracker.ai_generator import generate_monster, MonsterGenerationError
    backend = _mock_backend(json.dumps([{"name": "Goblin"}]))
    with pytest.raises(MonsterGenerationError, match="not an object"):
        generate_monster(backend, "a goblin")


def test_generate_monster_missing_name_raises():
    from dnd_combat_tracker.ai_generator import generate_monster, MonsterGenerationError
    monster = {k: v for k, v in MINIMAL_MONSTER.items() if k != "name"}
    backend = _mock_backend(json.dumps(monster))
    with pytest.raises(MonsterGenerationError, match="no name"):
        generate_monster(backend, "a goblin")


def test_generate_monster_empty_name_raises():
    from dnd_combat_tracker.ai_generator import generate_monster, MonsterGenerationError
    monster = {**MINIMAL_MONSTER, "name": ""}
    backend = _mock_backend(json.dumps(monster))
    with pytest.raises(MonsterGenerationError, match="no name"):
        generate_monster(backend, "a goblin")
