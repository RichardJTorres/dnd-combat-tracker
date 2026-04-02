"""Tests for combat session database operations."""

import pytest
from dnd_combat_tracker.db import combat as db
from dnd_combat_tracker.db import encounters as enc_db


@pytest.fixture
def encounter(session):
    return enc_db.create_encounter(session, {"name": "Test Encounter"})


@pytest.fixture
def combatants_data():
    return [
        {
            "name": "Goblin 1",
            "combatant_type": "creature",
            "initiative": 15,
            "max_hp": 7,
            "current_hp": 7,
            "ac": 15,
        },
        {
            "name": "Goblin 2",
            "combatant_type": "creature",
            "initiative": 10,
            "max_hp": 7,
            "current_hp": 7,
            "ac": 15,
        },
        {
            "name": "Aria",
            "combatant_type": "character",
            "initiative": 18,
            "max_hp": 38,
            "current_hp": 38,
            "ac": 16,
        },
    ]


def test_start_combat(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    assert combat.id is not None
    assert combat.encounter_id == encounter.id
    assert combat.round_number == 1
    assert combat.is_active is True


def test_combatants_sorted_by_initiative(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    combatants = db.get_combatants(session, combat.id)

    assert len(combatants) == 3
    # Should be sorted by initiative descending: Aria(18), Goblin 1(15), Goblin 2(10)
    assert combatants[0].name == "Aria"
    assert combatants[0].initiative == 18
    assert combatants[1].name == "Goblin 1"
    assert combatants[2].name == "Goblin 2"


def test_get_combat_session(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    fetched = db.get_combat_session(session, combat.id)
    assert fetched is not None
    assert fetched.id == combat.id


def test_get_active_combat(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    active = db.get_active_combat(session, encounter.id)
    assert active is not None
    assert active.id == combat.id


def test_get_active_combat_none_when_ended(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    db.end_combat(session, combat.id)
    assert db.get_active_combat(session, encounter.id) is None


def test_update_combatant_hp(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    combatants = db.get_combatants(session, combat.id)
    goblin = combatants[1]  # Goblin 1

    updated = db.update_combatant(session, goblin.id, {"current_hp": 3})
    assert updated is not None
    assert updated.current_hp == 3
    assert updated.max_hp == 7  # Unchanged


def test_update_combatant_conditions(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    combatants = db.get_combatants(session, combat.id)
    goblin = combatants[1]

    import json
    updated = db.update_combatant(
        session, goblin.id, {"conditions": json.dumps(["Poisoned", "Prone"])}
    )
    assert updated.get_conditions() == ["Poisoned", "Prone"]


def test_next_turn_advances(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    combatants = db.get_combatants(session, combat.id)

    # Initially at sort_order 0 (Aria)
    assert combat.current_turn_index == 0

    updated = db.next_turn(session, combat.id)
    assert updated.current_turn_index == combatants[1].sort_order  # Goblin 1


def test_next_turn_wraps_to_new_round(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    assert combat.round_number == 1

    # Advance through all turns
    db.next_turn(session, combat.id)  # Goblin 1
    db.next_turn(session, combat.id)  # Goblin 2
    updated = db.next_turn(session, combat.id)  # Wrap -> Round 2

    assert updated.round_number == 2
    # Should be back at first combatant
    active = db.get_active_combatants(session, combat.id)
    assert updated.current_turn_index == active[0].sort_order


def test_end_combat(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    ended = db.end_combat(session, combat.id)
    assert ended.is_active is False


def test_combatant_conditions_default_empty(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    combatants = db.get_combatants(session, combat.id)
    assert combatants[0].get_conditions() == []


def test_active_combatants_excludes_inactive(session, encounter, combatants_data):
    combat = db.start_combat(session, encounter.id, combatants_data)
    combatants = db.get_combatants(session, combat.id)

    # Kill goblin 2
    db.update_combatant(session, combatants[2].id, {"is_active": False})

    active = db.get_active_combatants(session, combat.id)
    assert len(active) == 2
    assert all(c.is_active for c in active)
