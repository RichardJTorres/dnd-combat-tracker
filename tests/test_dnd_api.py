"""Tests for D&D 5e API integration — mapper and API endpoints."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from dnd_combat_tracker.dnd_api import map_monster


# ---------------------------------------------------------------------------
# Mapper unit tests (pure function, no HTTP)
# ---------------------------------------------------------------------------

GOBLIN_RESPONSE = {
    "index": "goblin",
    "name": "Goblin",
    "size": "Small",
    "type": "humanoid",
    "subtype": "goblinoid",
    "armor_class": [{"type": "armor", "value": 15}],
    "hit_points": 7,
    "hit_dice": "2d6",
    "speed": {"walk": "30 ft."},
    "strength": 8,
    "dexterity": 14,
    "constitution": 10,
    "intelligence": 10,
    "wisdom": 8,
    "charisma": 8,
    "damage_vulnerabilities": [],
    "damage_resistances": [],
    "damage_immunities": [],
    "condition_immunities": [],
    "senses": {"darkvision": "60 ft.", "passive_perception": 9},
    "languages": "Common, Goblin",
    "challenge_rating": 0.25,
    "special_abilities": [
        {
            "name": "Nimble Escape",
            "desc": "The goblin can take the Disengage or Hide action as a bonus action.",
        }
    ],
    "actions": [
        {
            "name": "Scimitar",
            "desc": "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.",
        }
    ],
    "legendary_actions": [],
    "reactions": [],
}

DRAGON_RESPONSE = {
    "index": "adult-black-dragon",
    "name": "Adult Black Dragon",
    "size": "Huge",
    "type": "dragon",
    "subtype": None,
    "armor_class": [{"type": "natural armor", "value": 19}],
    "hit_points": 195,
    "hit_dice": "17d12",
    "speed": {"walk": "40 ft.", "fly": "80 ft.", "swim": "40 ft."},
    "strength": 23,
    "dexterity": 14,
    "constitution": 21,
    "intelligence": 14,
    "wisdom": 13,
    "charisma": 17,
    "damage_vulnerabilities": [],
    "damage_resistances": [],
    "damage_immunities": ["acid"],
    "condition_immunities": [],
    "senses": {
        "blindsight": "60 ft.",
        "darkvision": "120 ft.",
        "passive_perception": 17,
    },
    "languages": "Common, Draconic",
    "challenge_rating": 14,
    "special_abilities": [],
    "actions": [],
    "legendary_actions": [
        {"name": "Detect", "desc": "The dragon makes a Wisdom (Perception) check."}
    ],
    "reactions": [],
}

LICH_RESPONSE = {
    "index": "lich",
    "name": "Lich",
    "size": "Medium",
    "type": "undead",
    "subtype": None,
    "armor_class": [{"type": "natural armor", "value": 17}],
    "hit_points": 135,
    "hit_dice": "18d8",
    "speed": {"walk": "30 ft."},
    "strength": 11,
    "dexterity": 16,
    "constitution": 16,
    "intelligence": 20,
    "wisdom": 14,
    "charisma": 16,
    "damage_vulnerabilities": [],
    "damage_resistances": ["cold", "lightning", "necrotic"],
    "damage_immunities": ["poison", "bludgeoning", "piercing", "slashing from nonmagical attacks"],
    "condition_immunities": [{"index": "charmed", "name": "Charmed"}, {"index": "poisoned", "name": "Poisoned"}],
    "senses": {"truesight": "120 ft.", "passive_perception": 12},
    "languages": "Common plus up to five other languages",
    "challenge_rating": 21,
    "special_abilities": [],
    "actions": [],
    "legendary_actions": [],
    "reactions": [],
}


def test_map_monster_basic_fields():
    result = map_monster(GOBLIN_RESPONSE)
    assert result["name"] == "Goblin"
    assert result["size"] == "Small"
    assert result["creature_type"] == "humanoid"
    assert result["cr"] == 0.25
    assert result["hp"] == 7
    assert result["hp_formula"] == "2d6"
    assert result["ac"] == 15
    assert result["source"] == "SRD 5.1"


def test_map_monster_ac_notes():
    result = map_monster(GOBLIN_RESPONSE)
    assert result["ac_notes"] == "armor"


def test_map_monster_natural_armor_notes():
    result = map_monster(DRAGON_RESPONSE)
    assert result["ac_notes"] == "natural armor"


def test_map_monster_speed_walk_only():
    result = map_monster(GOBLIN_RESPONSE)
    assert result["speed"] == "30 ft."


def test_map_monster_speed_multiple():
    result = map_monster(DRAGON_RESPONSE)
    # Should include all speed types
    assert "40 ft." in result["speed"]
    assert "fly 80 ft." in result["speed"]
    assert "swim 40 ft." in result["speed"]


def test_map_monster_ability_scores():
    result = map_monster(GOBLIN_RESPONSE)
    assert result["strength"] == 8
    assert result["dexterity"] == 14
    assert result["constitution"] == 10
    assert result["intelligence"] == 10
    assert result["wisdom"] == 8
    assert result["charisma"] == 8


def test_map_monster_senses():
    result = map_monster(GOBLIN_RESPONSE)
    assert "darkvision 60 ft." in result["senses"]
    assert "passive Perception 9" in result["senses"]


def test_map_monster_senses_multiple():
    result = map_monster(DRAGON_RESPONSE)
    assert "blindsight 60 ft." in result["senses"]
    assert "darkvision 120 ft." in result["senses"]
    assert "passive Perception 17" in result["senses"]


def test_map_monster_languages():
    result = map_monster(GOBLIN_RESPONSE)
    assert result["languages"] == "Common, Goblin"


def test_map_monster_damage_immunities():
    result = map_monster(DRAGON_RESPONSE)
    assert result["damage_immunities"] == "acid"


def test_map_monster_damage_resistances():
    result = map_monster(LICH_RESPONSE)
    resistances = result["damage_resistances"]
    assert "cold" in resistances
    assert "lightning" in resistances
    assert "necrotic" in resistances


def test_map_monster_condition_immunities_objects():
    """Condition immunities can be objects with 'name' field."""
    result = map_monster(LICH_RESPONSE)
    conds = result["condition_immunities"]
    assert "Charmed" in conds
    assert "Poisoned" in conds


def test_map_monster_traits():
    result = map_monster(GOBLIN_RESPONSE)
    traits = json.loads(result["traits"])
    assert len(traits) == 1
    assert traits[0]["name"] == "Nimble Escape"
    assert "bonus action" in traits[0]["description"]


def test_map_monster_actions():
    result = map_monster(GOBLIN_RESPONSE)
    actions = json.loads(result["actions"])
    assert len(actions) == 1
    assert actions[0]["name"] == "Scimitar"
    assert "+4 to hit" in actions[0]["description"]


def test_map_monster_legendary_actions():
    result = map_monster(DRAGON_RESPONSE)
    legendary = json.loads(result["legendary_actions"])
    assert len(legendary) == 1
    assert legendary[0]["name"] == "Detect"


def test_map_monster_empty_actions():
    result = map_monster(DRAGON_RESPONSE)
    actions = json.loads(result["actions"])
    assert actions == []


def test_map_monster_no_damage_immunities():
    result = map_monster(GOBLIN_RESPONSE)
    assert result["damage_immunities"] is None or result["damage_immunities"] == ""


def test_map_monster_high_cr():
    result = map_monster(LICH_RESPONSE)
    assert result["cr"] == 21


# ---------------------------------------------------------------------------
# API endpoint tests (mock httpx)
# ---------------------------------------------------------------------------

MOCK_LIST_RESPONSE = {
    "count": 2,
    "results": [
        {"index": "goblin", "name": "Goblin", "url": "/api/2014/monsters/goblin"},
        {"index": "orc", "name": "Orc", "url": "/api/2014/monsters/orc"},
    ],
}


def test_search_monsters(client):
    """Search endpoint proxies D&D API and returns name/index list."""
    with patch("dnd_combat_tracker.dnd_api.search_monsters") as mock_search:
        mock_search.return_value = MOCK_LIST_RESPONSE["results"]
        r = client.get("/api/dnd/monsters?search=goblin")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert results[0]["name"] == "Goblin"
    assert results[0]["index"] == "goblin"


def test_search_monsters_empty_query(client):
    """Empty search returns results (browsing mode)."""
    with patch("dnd_combat_tracker.dnd_api.search_monsters") as mock_search:
        mock_search.return_value = MOCK_LIST_RESPONSE["results"]
        r = client.get("/api/dnd/monsters")
    assert r.status_code == 200


def test_import_monster(client):
    """Import endpoint fetches from API, maps, saves to DB, returns creature."""
    with patch("dnd_combat_tracker.dnd_api.fetch_monster") as mock_fetch:
        mock_fetch.return_value = GOBLIN_RESPONSE
        r = client.post("/api/dnd/monsters/goblin/import")
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Goblin"
    assert body["cr"] == 0.25
    assert body["hp"] == 7
    assert body["ac"] == 15
    assert body["id"] is not None  # Saved to DB


def test_import_monster_deduplicates(client):
    """Importing the same monster twice returns the existing creature."""
    with patch("dnd_combat_tracker.dnd_api.fetch_monster") as mock_fetch:
        mock_fetch.return_value = GOBLIN_RESPONSE
        r1 = client.post("/api/dnd/monsters/goblin/import")
        r2 = client.post("/api/dnd/monsters/goblin/import")
    assert r1.status_code == 201
    assert r2.status_code == 200
    # Same creature ID
    assert r1.json()["id"] == r2.json()["id"]


def test_import_monster_not_found(client):
    """Returns 404 if the D&D API doesn't know the monster."""
    with patch("dnd_combat_tracker.dnd_api.fetch_monster") as mock_fetch:
        mock_fetch.return_value = None
        r = client.post("/api/dnd/monsters/fake-monster/import")
    assert r.status_code == 404
