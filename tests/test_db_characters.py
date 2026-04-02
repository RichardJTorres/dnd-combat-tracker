"""Tests for player character database operations."""

from dnd_combat_tracker.db import characters as db


def test_create_character(session, sample_character_data):
    char = db.create_character(session, sample_character_data)
    assert char.id is not None
    assert char.name == "Aria Swiftwind"
    assert char.level == 5
    assert char.max_hp == 38
    assert char.ac == 16


def test_get_character(session, sample_character_data):
    created = db.create_character(session, sample_character_data)
    fetched = db.get_character(session, created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_character_not_found(session):
    assert db.get_character(session, 9999) is None


def test_list_characters_empty(session):
    assert db.list_characters(session) == []


def test_list_characters(session, sample_character_data):
    db.create_character(session, sample_character_data)
    db.create_character(
        session,
        {**sample_character_data, "name": "Baern Stonefist", "character_class": "Fighter"},
    )
    result = db.list_characters(session)
    assert len(result) == 2
    # Sorted by name
    assert result[0].name == "Aria Swiftwind"
    assert result[1].name == "Baern Stonefist"


def test_update_character(session, sample_character_data):
    char = db.create_character(session, sample_character_data)
    updated = db.update_character(session, char.id, {"current_hp": 20, "level": 6})
    assert updated is not None
    assert updated.current_hp == 20
    assert updated.level == 6
    assert updated.max_hp == 38  # Unchanged


def test_update_character_not_found(session):
    assert db.update_character(session, 9999, {"current_hp": 5}) is None


def test_delete_character(session, sample_character_data):
    char = db.create_character(session, sample_character_data)
    assert db.delete_character(session, char.id) is True
    assert db.get_character(session, char.id) is None


def test_delete_character_not_found(session):
    assert db.delete_character(session, 9999) is False


def test_character_defaults(session):
    char = db.create_character(session, {"name": "Unnamed Hero", "character_class": "Wizard"})
    assert char.level == 1
    assert char.max_hp == 10
    assert char.current_hp == 10
    assert char.ac == 10
    assert char.initiative_bonus == 0
    assert char.temp_hp == 0
