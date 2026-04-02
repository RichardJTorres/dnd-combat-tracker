"""API-level tests for AI monster generation endpoint."""

import json
import pytest
from unittest.mock import patch, MagicMock


GENERATED_CREATURE = {
    "name": "Cinder Goblin",
    "size": "Small",
    "creature_type": "humanoid",
    "cr": 1.0,
    "hp": 14,
    "hp_formula": "4d6",
    "ac": 13,
    "ac_notes": "natural armor",
    "speed": "30 ft.",
    "strength": 8,
    "dexterity": 14,
    "constitution": 10,
    "intelligence": 10,
    "wisdom": 8,
    "charisma": 10,
    "damage_immunities": "fire",
    "traits": json.dumps([{"name": "Fire Body", "description": "Deals 2 fire damage to any creature that touches it."}]),
    "actions": json.dumps([{"name": "Ember Claw", "description": "+4 to hit, 1d4+2 slashing plus 1d4 fire."}]),
    "source": "AI Generated",
}


def test_generate_monster_success(client):
    mock_backend = MagicMock()
    with patch("dnd_combat_tracker.api.routers.ai.get_backend", return_value=mock_backend), \
         patch("dnd_combat_tracker.api.routers.ai.generate_monster", return_value=GENERATED_CREATURE):
        r = client.post("/api/ai/generate-monster", json={"prompt": "a fire goblin", "cr": 1.0})

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Cinder Goblin"
    assert body["source"] == "AI Generated"


def test_generate_monster_response_has_required_fields(client):
    mock_backend = MagicMock()
    with patch("dnd_combat_tracker.api.routers.ai.get_backend", return_value=mock_backend), \
         patch("dnd_combat_tracker.api.routers.ai.generate_monster", return_value=GENERATED_CREATURE):
        r = client.post("/api/ai/generate-monster", json={"prompt": "a fire goblin", "cr": 1.0})

    body = r.json()
    for field in ("name", "cr", "hp", "ac", "size", "creature_type"):
        assert field in body, f"Missing field: {field}"


def test_generate_monster_cr_passed_to_generator(client):
    """The endpoint must forward the requested CR to generate_monster."""
    mock_backend = MagicMock()
    with patch("dnd_combat_tracker.api.routers.ai.get_backend", return_value=mock_backend) as _, \
         patch("dnd_combat_tracker.api.routers.ai.generate_monster", return_value=GENERATED_CREATURE) as mock_gen:
        client.post("/api/ai/generate-monster", json={"prompt": "a fire goblin", "cr": 1.0})
    mock_gen.assert_called_once()
    _, kwargs = mock_gen.call_args
    assert kwargs.get("cr") == 1.0 or mock_gen.call_args[0][2] == 1.0


def test_generate_monster_empty_prompt_returns_422(client):
    r = client.post("/api/ai/generate-monster", json={"prompt": "", "cr": 1})
    assert r.status_code == 422


def test_generate_monster_whitespace_prompt_returns_422(client):
    r = client.post("/api/ai/generate-monster", json={"prompt": "   ", "cr": 1})
    assert r.status_code == 422


def test_generate_monster_missing_cr_returns_422(client):
    r = client.post("/api/ai/generate-monster", json={"prompt": "a goblin"})
    assert r.status_code == 422


def test_generate_monster_invalid_cr_returns_422(client):
    r = client.post("/api/ai/generate-monster", json={"prompt": "a goblin", "cr": 99})
    assert r.status_code == 422


def test_generate_monster_no_api_key_returns_503(client):
    with patch("dnd_combat_tracker.api.routers.ai.get_backend",
               side_effect=ValueError("Anthropic API key not configured")):
        r = client.post("/api/ai/generate-monster", json={"prompt": "a goblin", "cr": 1})
    assert r.status_code == 503
    assert "API key" in r.json()["detail"]


def test_generate_monster_unknown_provider_returns_503(client):
    with patch("dnd_combat_tracker.api.routers.ai.get_backend",
               side_effect=ValueError("Unknown provider: 'fake'")):
        r = client.post("/api/ai/generate-monster", json={"prompt": "a goblin", "cr": 1})
    assert r.status_code == 503


def test_generate_monster_malformed_llm_output_returns_502(client):
    from dnd_combat_tracker.ai_generator import MonsterGenerationError
    mock_backend = MagicMock()
    with patch("dnd_combat_tracker.api.routers.ai.get_backend", return_value=mock_backend), \
         patch("dnd_combat_tracker.api.routers.ai.generate_monster",
               side_effect=MonsterGenerationError("LLM returned non-JSON")):
        r = client.post("/api/ai/generate-monster", json={"prompt": "a goblin", "cr": 1})
    assert r.status_code == 502
    assert "non-JSON" in r.json()["detail"]


def test_generate_monster_does_not_save_to_db(client):
    """Generation endpoint must not persist — only preview."""
    mock_backend = MagicMock()
    with patch("dnd_combat_tracker.api.routers.ai.get_backend", return_value=mock_backend), \
         patch("dnd_combat_tracker.api.routers.ai.generate_monster", return_value=GENERATED_CREATURE):
        client.post("/api/ai/generate-monster", json={"prompt": "a fire goblin", "cr": 1.0})

    # Creature should NOT be in the bestiary
    r = client.get("/api/creatures")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "Cinder Goblin" not in names
