"""Shared test fixtures."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine
from fastapi.testclient import TestClient


@pytest.fixture(name="engine", scope="function")
def engine_fixture():
    """In-memory SQLite engine using StaticPool so all connections share one DB."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import dnd_combat_tracker.db.models  # noqa: F401 - register models

    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)


@pytest.fixture(name="session")
def session_fixture(engine):
    """DB session connected to the in-memory engine."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    """FastAPI test client with the in-memory DB session injected."""
    from dnd_combat_tracker.api.app import app
    from dnd_combat_tracker.db.engine import get_session

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_creature_data():
    return {
        "name": "Goblin",
        "size": "Small",
        "creature_type": "humanoid",
        "cr": 0.25,
        "hp": 7,
        "hp_formula": "2d6",
        "ac": 15,
        "ac_notes": "leather armor, shield",
        "speed": "30 ft.",
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 8,
        "charisma": 8,
        "senses": "darkvision 60 ft., passive Perception 9",
        "languages": "Common, Goblin",
        "source": "Monster Manual",
    }


@pytest.fixture
def sample_character_data():
    return {
        "name": "Aria Swiftwind",
        "player_name": "Alice",
        "character_class": "Ranger",
        "level": 5,
        "race": "Wood Elf",
        "max_hp": 38,
        "current_hp": 38,
        "ac": 16,
        "initiative_bonus": 3,
        "dexterity": 16,
        "wisdom": 14,
        "passive_perception": 15,
    }
