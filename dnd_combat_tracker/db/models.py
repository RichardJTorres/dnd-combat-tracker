"""SQLModel table definitions for D&D Combat Tracker."""

import json
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Creature(SQLModel, table=True):
    """A bookmarked creature (monster/NPC) from the bestiary."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    size: str = "Medium"  # Tiny, Small, Medium, Large, Huge, Gargantuan
    creature_type: str = "beast"  # beast, undead, humanoid, dragon, etc.
    cr: float = 0.0  # 0, 0.125, 0.25, 0.5, 1-30
    hp: int = 1
    hp_formula: Optional[str] = None  # e.g. "4d8+4"
    ac: int = 10
    ac_notes: Optional[str] = None  # e.g. "natural armor"
    speed: str = "30 ft."

    # Ability scores
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # JSON string fields
    saving_throws: Optional[str] = None  # e.g. '{"dex": 4, "wis": 2}'
    skills: Optional[str] = None  # e.g. '{"perception": 4, "stealth": 6}'
    damage_vulnerabilities: Optional[str] = None
    damage_resistances: Optional[str] = None
    damage_immunities: Optional[str] = None
    condition_immunities: Optional[str] = None
    senses: Optional[str] = None  # e.g. "darkvision 60 ft., passive Perception 14"
    languages: Optional[str] = None
    traits: Optional[str] = None  # JSON array of {name, description}
    actions: Optional[str] = None  # JSON array of {name, description}
    bonus_actions: Optional[str] = None  # JSON array of {name, description}
    reactions: Optional[str] = None  # JSON array of {name, description}
    legendary_actions: Optional[str] = None  # JSON array of {name, description}

    source: Optional[str] = None  # e.g. "Monster Manual", "Custom"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def cr_display(self) -> str:
        """Human-readable CR (e.g. 0.125 -> '1/8')."""
        mapping = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
        if self.cr in mapping:
            return mapping[self.cr]
        if self.cr == int(self.cr):
            return str(int(self.cr))
        return str(self.cr)


class PlayerCharacter(SQLModel, table=True):
    """A player character in the party."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    player_name: Optional[str] = None
    character_class: str = "Fighter"
    subclass: Optional[str] = None
    level: int = 1
    race: Optional[str] = None

    max_hp: int = 10
    current_hp: int = 10
    temp_hp: int = 0
    ac: int = 10
    initiative_bonus: int = 0
    speed: int = 30

    # Ability scores
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    passive_perception: int = 10
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Encounter(SQLModel, table=True):
    """A named collection of creatures and characters that form a combat scenario."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EncounterParticipant(SQLModel, table=True):
    """A creature or character that is part of an encounter definition."""

    id: Optional[int] = Field(default=None, primary_key=True)
    encounter_id: int = Field(foreign_key="encounter.id")
    participant_type: str  # "creature" or "character"
    creature_id: Optional[int] = Field(default=None, foreign_key="creature.id")
    character_id: Optional[int] = Field(
        default=None, foreign_key="playercharacter.id"
    )
    quantity: int = 1  # How many of this creature (ignored for characters)


class CombatSession(SQLModel, table=True):
    """An active or completed combat run of an encounter."""

    id: Optional[int] = Field(default=None, primary_key=True)
    encounter_id: int = Field(foreign_key="encounter.id")
    round_number: int = 1
    current_turn_index: int = 0
    is_active: bool = True
    started_at: datetime = Field(default_factory=datetime.utcnow)


# Standard 5e/5.5e conditions
CONDITIONS = [
    "Blinded",
    "Charmed",
    "Deafened",
    "Exhaustion",
    "Frightened",
    "Grappled",
    "Incapacitated",
    "Invisible",
    "Paralyzed",
    "Petrified",
    "Poisoned",
    "Prone",
    "Restrained",
    "Stunned",
    "Unconscious",
]


class AppSetting(SQLModel, table=True):
    """Key/value store for application settings (provider, model names, etc.)."""

    key: str = Field(primary_key=True)
    value: str


class Combatant(SQLModel, table=True):
    """An individual combatant instance within a combat session."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="combatsession.id")
    name: str
    combatant_type: str  # "creature" or "character"
    source_id: Optional[int] = None  # creature_id or character_id
    initiative: int = 0  # Final initiative value (d20 + bonus)
    max_hp: int = 1
    current_hp: int = 1
    temp_hp: int = 0
    ac: int = 10
    conditions: str = "[]"  # JSON array of condition strings
    is_active: bool = True  # False if dead/fled/removed
    notes: Optional[str] = None
    sort_order: int = 0  # Position in initiative order (0 = first)

    def get_conditions(self) -> list[str]:
        return json.loads(self.conditions)

    def set_conditions(self, conditions: list[str]) -> None:
        self.conditions = json.dumps(conditions)
