from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from dnd_combat_tracker.db.models import Encounter, EncounterParticipant


def create_encounter(session: Session, data: dict) -> Encounter:
    encounter = Encounter(**data)
    session.add(encounter)
    session.commit()
    session.refresh(encounter)
    return encounter


def get_encounter(session: Session, encounter_id: int) -> Optional[Encounter]:
    return session.get(Encounter, encounter_id)


def list_encounters(session: Session) -> list[Encounter]:
    stmt = select(Encounter).order_by(Encounter.updated_at.desc())
    return list(session.exec(stmt).all())


def update_encounter(
    session: Session, encounter_id: int, data: dict
) -> Optional[Encounter]:
    encounter = session.get(Encounter, encounter_id)
    if not encounter:
        return None
    for key, value in data.items():
        setattr(encounter, key, value)
    encounter.updated_at = datetime.utcnow()
    session.add(encounter)
    session.commit()
    session.refresh(encounter)
    return encounter


def delete_encounter(session: Session, encounter_id: int) -> bool:
    encounter = session.get(Encounter, encounter_id)
    if not encounter:
        return False
    # Remove participants first
    stmt = select(EncounterParticipant).where(
        EncounterParticipant.encounter_id == encounter_id
    )
    for p in session.exec(stmt).all():
        session.delete(p)
    session.delete(encounter)
    session.commit()
    return True


def add_participant(session: Session, encounter_id: int, data: dict) -> EncounterParticipant:
    participant = EncounterParticipant(encounter_id=encounter_id, **data)
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return participant


def get_participants(session: Session, encounter_id: int) -> list[EncounterParticipant]:
    stmt = select(EncounterParticipant).where(
        EncounterParticipant.encounter_id == encounter_id
    )
    return list(session.exec(stmt).all())


def remove_participant(session: Session, participant_id: int) -> bool:
    participant = session.get(EncounterParticipant, participant_id)
    if not participant:
        return False
    session.delete(participant)
    session.commit()
    return True
