"""D&D 5e SRD API integration — fetching and mapping monster data."""

import json
from typing import Optional

import httpx

BASE_URL = "https://www.dnd5eapi.co/api/2014"


def map_monster(data: dict) -> dict:
    """Map a D&D API monster response to our Creature schema dict."""

    # AC — first entry wins
    ac_entry = data.get("armor_class", [{}])[0] if data.get("armor_class") else {}
    ac = ac_entry.get("value", 10)
    ac_notes = ac_entry.get("type") or None

    # Speed — walk only becomes plain "30 ft.", multiple become "30 ft., fly 60 ft."
    speed_obj = data.get("speed", {})
    speed_parts = []
    for mode, value in speed_obj.items():
        if value:
            if mode == "walk":
                speed_parts.insert(0, value)  # walk first, no label
            else:
                speed_parts.append(f"{mode} {value}")
    speed = ", ".join(speed_parts) if speed_parts else "30 ft."

    # Senses — build "darkvision 60 ft., passive Perception 9"
    senses_obj = data.get("senses", {})
    sense_parts = []
    for key, val in senses_obj.items():
        if key == "passive_perception":
            sense_parts.append(f"passive Perception {val}")
        elif val:
            sense_parts.append(f"{key.replace('_', ' ')} {val}")
    senses = ", ".join(sense_parts) if sense_parts else None

    # Damage/condition lists — items may be strings or objects with "name"
    def _join_list(items: list) -> Optional[str]:
        if not items:
            return None
        parts = [i["name"] if isinstance(i, dict) else i for i in items]
        return ", ".join(parts)

    # Traits / actions / legendary / reactions — stored as JSON [{name, description}]
    def _map_ability_list(items: list) -> str:
        return json.dumps(
            [{"name": i["name"], "description": i.get("desc", "")} for i in items]
        )

    return {
        "name": data["name"],
        "size": data.get("size", "Medium"),
        "creature_type": data.get("type", "beast"),
        "cr": float(data.get("challenge_rating", 0)),
        "hp": data.get("hit_points", 1),
        "hp_formula": data.get("hit_dice") or None,
        "ac": ac,
        "ac_notes": ac_notes,
        "speed": speed,
        "strength": data.get("strength", 10),
        "dexterity": data.get("dexterity", 10),
        "constitution": data.get("constitution", 10),
        "intelligence": data.get("intelligence", 10),
        "wisdom": data.get("wisdom", 10),
        "charisma": data.get("charisma", 10),
        "senses": senses,
        "languages": data.get("languages") or None,
        "damage_vulnerabilities": _join_list(data.get("damage_vulnerabilities", [])),
        "damage_resistances": _join_list(data.get("damage_resistances", [])),
        "damage_immunities": _join_list(data.get("damage_immunities", [])),
        "condition_immunities": _join_list(data.get("condition_immunities", [])),
        "traits": _map_ability_list(data.get("special_abilities", [])),
        "actions": _map_ability_list(data.get("actions", [])),
        "reactions": _map_ability_list(data.get("reactions", [])),
        "legendary_actions": _map_ability_list(data.get("legendary_actions", [])),
        "source": "SRD 5.1",
    }


def search_monsters(query: str = "") -> list[dict]:
    """Fetch monster list from the D&D API, optionally filtered by name prefix."""
    params = {}
    if query:
        # The API supports filtering by name with ?name=
        params["name"] = query
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{BASE_URL}/monsters", params=params)
        r.raise_for_status()
        data = r.json()
    results = data.get("results", [])
    # Client-side filter for partial matches (API only supports prefix match)
    if query:
        q = query.lower()
        results = [m for m in results if q in m["name"].lower()]
    return [{"index": m["index"], "name": m["name"]} for m in results]


def fetch_monster(index: str) -> Optional[dict]:
    """Fetch a single monster by index from the D&D API. Returns None if not found."""
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{BASE_URL}/monsters/{index}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
