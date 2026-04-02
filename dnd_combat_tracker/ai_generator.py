"""AI-powered monster generation."""

import json
import re

from dnd_combat_tracker.backends.base import BaseBackend

SYSTEM_PROMPT = """You are a D&D 5.5e monster designer. When given a description of a monster, respond with ONLY a valid JSON object — no prose, no markdown, no explanation, no code fences.

The JSON must have exactly these fields:

{
  "name": "<string>",
  "size": "<Tiny|Small|Medium|Large|Huge|Gargantuan>",
  "creature_type": "<aberration|beast|celestial|construct|dragon|elemental|fey|fiend|giant|humanoid|monstrosity|ooze|plant|undead>",
  "cr": <number: 0, 0.125, 0.25, 0.5, or 1-30>,
  "hp": <integer>,
  "hp_formula": "<string or null>",
  "ac": <integer>,
  "ac_notes": "<string or null>",
  "speed": "<string>",
  "strength": <integer 1-30>,
  "dexterity": <integer 1-30>,
  "constitution": <integer 1-30>,
  "intelligence": <integer 1-30>,
  "wisdom": <integer 1-30>,
  "charisma": <integer 1-30>,
  "saving_throws": "<JSON-encoded object string or null>",
  "skills": "<JSON-encoded object string or null>",
  "damage_vulnerabilities": "<comma-separated string or null>",
  "damage_resistances": "<comma-separated string or null>",
  "damage_immunities": "<comma-separated string or null>",
  "condition_immunities": "<comma-separated string or null>",
  "senses": "<string or null>",
  "languages": "<string or null>",
  "traits": "<JSON-encoded array string or null>",
  "actions": "<JSON-encoded array string or null>",
  "bonus_actions": "<JSON-encoded array string or null>",
  "reactions": "<JSON-encoded array string or null>",
  "legendary_actions": "<JSON-encoded array string or null>",
  "source": "AI Generated"
}

CRITICAL: traits, actions, bonus_actions, reactions, legendary_actions, saving_throws, and skills must be JSON-encoded STRINGS — not nested objects or arrays. Each element in the ability arrays must have "name" and "description" keys.

Example for traits: "[{\\"name\\": \\"Pack Tactics\\", \\"description\\": \\"The creature has advantage on attack rolls when an ally is adjacent to the target.\\"}]"

Use null for fields that do not apply. Ensure HP is consistent with hp_formula and the constitution modifier. Make the stat block balanced for the given CR. Output ONLY the JSON object."""

# Fields that must be stored as JSON-encoded strings (not native structures)
_ARRAY_FIELDS = ("traits", "actions", "bonus_actions", "reactions", "legendary_actions")
_OBJECT_FIELDS = ("saving_throws", "skills")

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


class MonsterGenerationError(Exception):
    """Raised when the LLM response cannot be parsed into a valid creature dict."""


def _extract_json(raw: str) -> str:
    """Strip markdown code fences if present, otherwise return stripped text."""
    m = _FENCE_RE.search(raw)
    return m.group(1) if m else raw.strip()


def _normalise(data: dict) -> dict:
    """
    Coerce known fields into the formats expected by the Creature model:
    - Array/object fields must be JSON-encoded strings (not native structures)
    - Empty lists/strings become None
    - source is always overridden to "AI Generated"
    """
    for field in _ARRAY_FIELDS:
        val = data.get(field)
        if isinstance(val, list):
            data[field] = json.dumps(val) if val else None
        elif isinstance(val, dict):
            data[field] = json.dumps([val])
        elif val == "":
            data[field] = None

    for field in _OBJECT_FIELDS:
        val = data.get(field)
        if isinstance(val, dict):
            data[field] = json.dumps(val) if val else None
        elif isinstance(val, list):
            data[field] = None
        elif val == "":
            data[field] = None

    # Coerce empty strings to None for all remaining string fields
    _STRING_FIELDS = (
        "damage_vulnerabilities", "damage_resistances", "damage_immunities",
        "condition_immunities", "senses", "languages", "hp_formula", "ac_notes",
    )
    for field in _STRING_FIELDS:
        if data.get(field) == "":
            data[field] = None

    # Always enforce source
    data["source"] = "AI Generated"

    return data


def generate_monster(backend: BaseBackend, prompt: str) -> dict:
    """
    Call the LLM backend with the monster generation system prompt and user
    description. Parse and normalise the response into a creature field dict
    suitable for passing to db.creatures.create_creature().

    Raises MonsterGenerationError if the response cannot be parsed.
    """
    raw = backend.stream_turn(SYSTEM_PROMPT, prompt, on_token=lambda _: None)
    text = _extract_json(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MonsterGenerationError(f"LLM returned non-JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise MonsterGenerationError("LLM returned JSON but not an object")

    if not data.get("name"):
        raise MonsterGenerationError("Generated creature has no name")

    return _normalise(data)
