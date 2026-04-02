from typing import Optional

from sqlmodel import Session, select

from dnd_combat_tracker.db.models import Creature


def create_creature(session: Session, data: dict) -> Creature:
    creature = Creature(**data)
    session.add(creature)
    session.commit()
    session.refresh(creature)
    return creature


def get_creature(session: Session, creature_id: int) -> Optional[Creature]:
    return session.get(Creature, creature_id)


def list_creatures(
    session: Session, search: Optional[str] = None, creature_type: Optional[str] = None
) -> list[Creature]:
    stmt = select(Creature)
    if search:
        stmt = stmt.where(Creature.name.ilike(f"%{search}%"))
    if creature_type:
        stmt = stmt.where(Creature.creature_type == creature_type)
    stmt = stmt.order_by(Creature.name)
    return list(session.exec(stmt).all())


def update_creature(
    session: Session, creature_id: int, data: dict
) -> Optional[Creature]:
    creature = session.get(Creature, creature_id)
    if not creature:
        return None
    for key, value in data.items():
        setattr(creature, key, value)
    session.add(creature)
    session.commit()
    session.refresh(creature)
    return creature


def delete_creature(session: Session, creature_id: int) -> bool:
    creature = session.get(Creature, creature_id)
    if not creature:
        return False
    session.delete(creature)
    session.commit()
    return True
