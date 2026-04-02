import json
from typing import Optional

from sqlmodel import Session, select

from dnd_combat_tracker.db.models import CombatSession, Combatant


def start_combat(
    session: Session, encounter_id: int, combatants_data: list[dict]
) -> CombatSession:
    """Create a new combat session and populate it with combatants sorted by initiative."""
    combat = CombatSession(encounter_id=encounter_id)
    session.add(combat)
    session.commit()
    session.refresh(combat)

    # Sort by initiative descending, then create combatants with sort_order
    sorted_combatants = sorted(
        combatants_data, key=lambda c: c.get("initiative", 0), reverse=True
    )
    for order, cdata in enumerate(sorted_combatants):
        combatant = Combatant(session_id=combat.id, sort_order=order, **cdata)
        session.add(combatant)

    session.commit()
    return combat


def get_combat_session(session: Session, session_id: int) -> Optional[CombatSession]:
    return session.get(CombatSession, session_id)


def get_active_combat(session: Session, encounter_id: int) -> Optional[CombatSession]:
    stmt = (
        select(CombatSession)
        .where(CombatSession.encounter_id == encounter_id)
        .where(CombatSession.is_active == True)
        .order_by(CombatSession.started_at.desc())
    )
    return session.exec(stmt).first()


def get_combatants(session: Session, session_id: int) -> list[Combatant]:
    stmt = (
        select(Combatant)
        .where(Combatant.session_id == session_id)
        .order_by(Combatant.sort_order)
    )
    return list(session.exec(stmt).all())


def get_active_combatants(session: Session, session_id: int) -> list[Combatant]:
    stmt = (
        select(Combatant)
        .where(Combatant.session_id == session_id)
        .where(Combatant.is_active == True)
        .order_by(Combatant.sort_order)
    )
    return list(session.exec(stmt).all())


def update_combatant(
    session: Session, combatant_id: int, data: dict
) -> Optional[Combatant]:
    combatant = session.get(Combatant, combatant_id)
    if not combatant:
        return None
    for key, value in data.items():
        setattr(combatant, key, value)
    session.add(combatant)
    session.commit()
    session.refresh(combatant)
    return combatant


def next_turn(session: Session, session_id: int) -> Optional[CombatSession]:
    """Advance to the next active combatant's turn, incrementing round as needed."""
    combat = session.get(CombatSession, session_id)
    if not combat or not combat.is_active:
        return None

    active = get_active_combatants(session, session_id)
    if not active:
        return combat

    current_idx = combat.current_turn_index
    # Find the next active combatant after the current index
    next_order = None
    for combatant in active:
        if combatant.sort_order > current_idx:
            next_order = combatant.sort_order
            break

    if next_order is None:
        # Wrap around to next round
        combat.round_number += 1
        next_order = active[0].sort_order

    combat.current_turn_index = next_order
    session.add(combat)
    session.commit()
    session.refresh(combat)
    return combat


def end_combat(session: Session, session_id: int) -> Optional[CombatSession]:
    combat = session.get(CombatSession, session_id)
    if not combat:
        return None
    combat.is_active = False
    session.add(combat)
    session.commit()
    session.refresh(combat)
    return combat
