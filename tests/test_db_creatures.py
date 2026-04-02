"""Tests for creature database operations."""

import pytest
from dnd_combat_tracker.db import creatures as db


def test_create_creature(session, sample_creature_data):
    creature = db.create_creature(session, sample_creature_data)
    assert creature.id is not None
    assert creature.name == "Goblin"
    assert creature.cr == 0.25
    assert creature.hp == 7
    assert creature.ac == 15


def test_get_creature(session, sample_creature_data):
    created = db.create_creature(session, sample_creature_data)
    fetched = db.get_creature(session, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Goblin"


def test_get_creature_not_found(session):
    assert db.get_creature(session, 9999) is None


def test_list_creatures_empty(session):
    assert db.list_creatures(session) == []


def test_list_creatures(session, sample_creature_data):
    db.create_creature(session, sample_creature_data)
    db.create_creature(session, {**sample_creature_data, "name": "Orc", "cr": 0.5})
    result = db.list_creatures(session)
    assert len(result) == 2
    # Should be sorted by name
    assert result[0].name == "Goblin"
    assert result[1].name == "Orc"


def test_list_creatures_search(session, sample_creature_data):
    db.create_creature(session, sample_creature_data)
    db.create_creature(session, {**sample_creature_data, "name": "Goblin Boss"})
    db.create_creature(session, {**sample_creature_data, "name": "Orc", "cr": 0.5})

    results = db.list_creatures(session, search="goblin")
    assert len(results) == 2
    assert all("Goblin" in r.name for r in results)


def test_list_creatures_by_type(session, sample_creature_data):
    db.create_creature(session, sample_creature_data)  # humanoid
    db.create_creature(
        session, {**sample_creature_data, "name": "Wolf", "creature_type": "beast"}
    )

    results = db.list_creatures(session, creature_type="beast")
    assert len(results) == 1
    assert results[0].name == "Wolf"


def test_update_creature(session, sample_creature_data):
    creature = db.create_creature(session, sample_creature_data)
    updated = db.update_creature(session, creature.id, {"hp": 14, "name": "Goblin Elite"})
    assert updated is not None
    assert updated.hp == 14
    assert updated.name == "Goblin Elite"
    # Other fields unchanged
    assert updated.ac == 15


def test_update_creature_not_found(session):
    result = db.update_creature(session, 9999, {"hp": 5})
    assert result is None


def test_delete_creature(session, sample_creature_data):
    creature = db.create_creature(session, sample_creature_data)
    assert db.delete_creature(session, creature.id) is True
    assert db.get_creature(session, creature.id) is None


def test_delete_creature_not_found(session):
    assert db.delete_creature(session, 9999) is False


def test_cr_display(session, sample_creature_data):
    creature = db.create_creature(session, {**sample_creature_data, "cr": 0.125})
    assert creature.cr_display == "1/8"

    creature2 = db.create_creature(session, {**sample_creature_data, "cr": 5.0})
    assert creature2.cr_display == "5"
