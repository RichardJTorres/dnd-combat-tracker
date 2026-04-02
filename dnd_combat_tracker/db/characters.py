from typing import Optional

from sqlmodel import Session, select

from dnd_combat_tracker.db.models import PlayerCharacter


def create_character(session: Session, data: dict) -> PlayerCharacter:
    character = PlayerCharacter(**data)
    session.add(character)
    session.commit()
    session.refresh(character)
    return character


def get_character(session: Session, character_id: int) -> Optional[PlayerCharacter]:
    return session.get(PlayerCharacter, character_id)


def list_characters(session: Session) -> list[PlayerCharacter]:
    stmt = select(PlayerCharacter).order_by(PlayerCharacter.name)
    return list(session.exec(stmt).all())


def update_character(
    session: Session, character_id: int, data: dict
) -> Optional[PlayerCharacter]:
    character = session.get(PlayerCharacter, character_id)
    if not character:
        return None
    for key, value in data.items():
        setattr(character, key, value)
    session.add(character)
    session.commit()
    session.refresh(character)
    return character


def delete_character(session: Session, character_id: int) -> bool:
    character = session.get(PlayerCharacter, character_id)
    if not character:
        return False
    session.delete(character)
    session.commit()
    return True
