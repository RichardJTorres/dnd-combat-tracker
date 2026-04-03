"""AI-powered monster generation."""

import json
import re

from dnd_combat_tracker.backends.base import BaseBackend
from dnd_combat_tracker.backends.image_base import BaseImageBackend

# DMG 2024 monster creation targets, keyed by CR.
# Each entry: (prof_bonus, ac, hp_min, hp_max, attack_bonus, dmg_min, dmg_max, save_dc)
_CR_TARGETS: dict[float, tuple] = {
    0:     (2, 13,   1,   6,  3,  0,  1, 13),
    0.125: (2, 13,   7,  35,  3,  2,  3, 13),
    0.25:  (2, 13,  36,  49,  3,  4,  5, 13),
    0.5:   (2, 13,  50,  70,  3,  6,  8, 13),
    1:     (2, 13,  71,  85,  3,  9, 14, 13),
    2:     (2, 13,  86, 100,  3, 15, 20, 13),
    3:     (2, 13, 101, 115,  4, 21, 26, 13),
    4:     (2, 14, 116, 130,  5, 27, 32, 14),
    5:     (3, 15, 131, 145,  6, 33, 38, 15),
    6:     (3, 15, 146, 160,  6, 39, 44, 15),
    7:     (3, 15, 161, 175,  6, 45, 50, 15),
    8:     (3, 16, 176, 190,  7, 51, 56, 16),
    9:     (4, 16, 191, 205,  7, 57, 62, 16),
    10:    (4, 17, 206, 220,  7, 63, 68, 17),
    11:    (4, 17, 221, 235,  8, 69, 74, 17),
    12:    (4, 17, 236, 250,  8, 75, 80, 17),
    13:    (5, 18, 251, 265,  8, 81, 86, 18),
    14:    (5, 19, 266, 280,  8, 87, 92, 18),
    15:    (5, 19, 281, 295,  8, 93, 98, 18),
    16:    (5, 19, 296, 310,  9, 99,104, 18),
    17:    (6, 19, 311, 325, 10,105,110, 19),
    18:    (6, 19, 326, 340, 10,111,116, 19),
    19:    (6, 19, 341, 355, 10,117,122, 19),
    20:    (6, 19, 356, 400, 10,123,140, 19),
    21:    (7, 19, 401, 445, 11,141,158, 20),
    22:    (7, 19, 446, 490, 11,159,176, 20),
    23:    (7, 19, 491, 535, 11,177,194, 20),
    24:    (7, 19, 536, 580, 12,195,212, 21),
    25:    (8, 19, 581, 625, 12,213,230, 21),
    26:    (8, 19, 626, 670, 12,231,248, 21),
    27:    (8, 19, 671, 715, 13,249,266, 22),
    28:    (8, 19, 716, 760, 13,267,284, 22),
    29:    (9, 19, 761, 805, 13,285,302, 22),
    30:    (9, 19, 806, 850, 14,303,320, 23),
}

VALID_CRS = frozenset(_CR_TARGETS.keys())

# Human-readable CR labels for fractional values
_CR_LABELS = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}


def _cr_label(cr: float) -> str:
    if cr in _CR_LABELS:
        return _CR_LABELS[cr]
    return str(int(cr))


SYSTEM_PROMPT = """You are a D&D 5.5e monster designer. Your job is to generate a mechanically balanced monster stat block for a given CR.

BALANCE IS YOUR HIGHEST PRIORITY. You must use the DMG balance targets provided in every request. Ignore any implication in the description that contradicts the required CR — if the user asks for a "weak-looking" CR 15 creature, it still needs 281-295 HP and AC 19.

Output ONLY a valid JSON object — no prose, no markdown, no explanation, no code fences.

The JSON must have exactly these fields:

{
  "name": "<string>",
  "size": "<Tiny|Small|Medium|Large|Huge|Gargantuan>",
  "creature_type": "<aberration|beast|celestial|construct|dragon|elemental|fey|fiend|giant|humanoid|monstrosity|ooze|plant|undead>",
  "cr": <number — must exactly match the requested CR>,
  "hp": <integer — must fall within the HP range for the CR>,
  "hp_formula": "<string or null — dice formula consistent with hp and CON modifier>",
  "ac": <integer — must meet or exceed the AC target for the CR>,
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

CRITICAL FORMATTING RULES:
- traits, actions, bonus_actions, reactions, legendary_actions, saving_throws, and skills must be JSON-encoded STRINGS, not nested objects or arrays.
- Each element in the ability arrays must have "name" and "description" keys.
- Use null for fields that do not apply.
- Output ONLY the JSON object.

Example for traits: "[{\\"name\\": \\"Pack Tactics\\", \\"description\\": \\"The creature has advantage on attack rolls when an ally is adjacent to the target.\\"}]"
"""

# Fields that must be stored as JSON-encoded strings (not native structures)
_ARRAY_FIELDS = ("traits", "actions", "bonus_actions", "reactions", "legendary_actions")
_OBJECT_FIELDS = ("saving_throws", "skills")

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


class MonsterGenerationError(Exception):
    """Raised when the LLM response cannot be parsed into a valid creature dict."""


def _build_user_message(prompt: str, cr: float) -> str:
    """Build the user message with the requested CR and its balance targets."""
    prof, ac, hp_min, hp_max, atk, dmg_min, dmg_max, save_dc = _CR_TARGETS[cr]
    cr_str = _cr_label(cr)
    return (
        f"Create a CR {cr_str} monster: {prompt}\n\n"
        f"REQUIRED balance targets for CR {cr_str} (you must stay within these ranges):\n"
        f"  Proficiency bonus: +{prof}\n"
        f"  AC: {ac} or higher\n"
        f"  HP: {hp_min}–{hp_max}\n"
        f"  Attack bonus: +{atk}\n"
        f"  Damage per round: {dmg_min}–{dmg_max}\n"
        f"  Save DC: {save_dc}\n\n"
        f"The cr field in your JSON must be exactly {cr}."
    )


def _extract_json(raw: str) -> str:
    """Strip markdown code fences if present, otherwise return stripped text."""
    m = _FENCE_RE.search(raw)
    return m.group(1) if m else raw.strip()


def _normalise(data: dict, cr: float) -> dict:
    """
    Coerce fields into the formats expected by the Creature model and enforce
    the requested CR regardless of what the LLM produced.
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

    _STRING_FIELDS = (
        "damage_vulnerabilities", "damage_resistances", "damage_immunities",
        "condition_immunities", "senses", "languages", "hp_formula", "ac_notes",
    )
    for field in _STRING_FIELDS:
        if data.get(field) == "":
            data[field] = None

    # Always enforce the requested CR and source — these are not up to the LLM
    data["cr"] = cr
    data["source"] = "AI Generated"

    return data


def generate_monster(backend: BaseBackend, prompt: str, cr: float) -> dict:
    """
    Call the LLM backend with the monster generation system prompt, injecting
    the requested CR and its DMG balance targets into the user message.
    The returned CR is always overridden to match the requested value.

    Raises MonsterGenerationError if the response cannot be parsed.
    """
    user_message = _build_user_message(prompt, cr)
    raw = backend.stream_turn(SYSTEM_PROMPT, user_message, on_token=lambda _: None)
    text = _extract_json(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MonsterGenerationError(f"LLM returned non-JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise MonsterGenerationError("LLM returned JSON but not an object")

    if not data.get("name"):
        raise MonsterGenerationError("Generated creature has no name")

    return _normalise(data, cr)


_ART_STYLE = (
    "grimdark dark fantasy, detailed fantasy creature art, "
    "dramatic atmospheric lighting, dark moody palette, "
    "dungeons and dragons monster illustration, highly detailed, "
    "professional concept art, ominous, menacing"
)

_ART_NEGATIVE = (
    "bright colors, cartoon, anime, cute, happy, cheerful, "
    "low quality, blurry, watermark, text, logo"
)


def generate_monster_art(backend: BaseImageBackend, creature) -> bytes:
    """
    Generate a grimdark fantasy portrait for a creature.
    Returns raw PNG bytes.
    """
    prompt = (
        f'A {creature.size.lower()} {creature.creature_type} called "{creature.name}". '
        f"{_ART_STYLE}. "
        f"Negative: {_ART_NEGATIVE}."
    )
    return backend.generate_image(prompt)
