"""Tests for encounter database operations."""

from dnd_combat_tracker.db import encounters as db
from dnd_combat_tracker.db import creatures as creature_db
from dnd_combat_tracker.db import characters as character_db


def test_create_encounter(session):
    enc = db.create_encounter(session, {"name": "Goblin Ambush"})
    assert enc.id is not None
    assert enc.name == "Goblin Ambush"
    assert enc.description is None


def test_create_encounter_with_description(session):
    enc = db.create_encounter(
        session, {"name": "Dragon Lair", "description": "The party enters a volcanic cavern."}
    )
    assert enc.description == "The party enters a volcanic cavern."


def test_get_encounter(session):
    created = db.create_encounter(session, {"name": "Test Encounter"})
    fetched = db.get_encounter(session, created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_encounter_not_found(session):
    assert db.get_encounter(session, 9999) is None


def test_list_encounters(session):
    db.create_encounter(session, {"name": "Encounter A"})
    db.create_encounter(session, {"name": "Encounter B"})
    result = db.list_encounters(session)
    assert len(result) == 2


def test_update_encounter(session):
    enc = db.create_encounter(session, {"name": "Old Name"})
    updated = db.update_encounter(session, enc.id, {"name": "New Name"})
    assert updated is not None
    assert updated.name == "New Name"


def test_delete_encounter(session):
    enc = db.create_encounter(session, {"name": "To Delete"})
    assert db.delete_encounter(session, enc.id) is True
    assert db.get_encounter(session, enc.id) is None


def test_delete_encounter_cascades_participants(session, sample_creature_data):
    enc = db.create_encounter(session, {"name": "With Participants"})
    creature = creature_db.create_creature(session, sample_creature_data)
    db.add_participant(
        session, enc.id, {"participant_type": "creature", "creature_id": creature.id, "quantity": 3}
    )
    assert len(db.get_participants(session, enc.id)) == 1
    db.delete_encounter(session, enc.id)
    # Participants should be removed
    assert db.get_encounter(session, enc.id) is None


def test_add_creature_participant(session, sample_creature_data):
    enc = db.create_encounter(session, {"name": "Goblin Fight"})
    creature = creature_db.create_creature(session, sample_creature_data)

    participant = db.add_participant(
        session,
        enc.id,
        {"participant_type": "creature", "creature_id": creature.id, "quantity": 4},
    )
    assert participant.id is not None
    assert participant.encounter_id == enc.id
    assert participant.participant_type == "creature"
    assert participant.creature_id == creature.id
    assert participant.quantity == 4


def test_add_character_participant(session, sample_character_data):
    enc = db.create_encounter(session, {"name": "Party Fight"})
    char = character_db.create_character(session, sample_character_data)

    participant = db.add_participant(
        session,
        enc.id,
        {"participant_type": "character", "character_id": char.id},
    )
    assert participant.participant_type == "character"
    assert participant.character_id == char.id
    assert participant.quantity == 1


def test_get_participants(session, sample_creature_data, sample_character_data):
    enc = db.create_encounter(session, {"name": "Mixed Fight"})
    creature = creature_db.create_creature(session, sample_creature_data)
    char = character_db.create_character(session, sample_character_data)

    db.add_participant(
        session, enc.id, {"participant_type": "creature", "creature_id": creature.id, "quantity": 2}
    )
    db.add_participant(
        session, enc.id, {"participant_type": "character", "character_id": char.id}
    )

    participants = db.get_participants(session, enc.id)
    assert len(participants) == 2


def test_remove_participant(session, sample_creature_data):
    enc = db.create_encounter(session, {"name": "Test"})
    creature = creature_db.create_creature(session, sample_creature_data)
    p = db.add_participant(
        session, enc.id, {"participant_type": "creature", "creature_id": creature.id}
    )

    assert db.remove_participant(session, p.id) is True
    assert db.get_participants(session, enc.id) == []
