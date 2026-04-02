from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db import encounters as db

router = APIRouter(prefix="/encounters", tags=["encounters"])


@router.get("")
def list_encounters(session: Session = Depends(get_session)):
    return db.list_encounters(session)


@router.post("", status_code=201)
def create_encounter(data: dict, session: Session = Depends(get_session)):
    return db.create_encounter(session, data)


@router.get("/{encounter_id}")
def get_encounter(encounter_id: int, session: Session = Depends(get_session)):
    encounter = db.get_encounter(session, encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter


@router.patch("/{encounter_id}")
def update_encounter(
    encounter_id: int, data: dict, session: Session = Depends(get_session)
):
    encounter = db.update_encounter(session, encounter_id, data)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter


@router.delete("/{encounter_id}", status_code=204)
def delete_encounter(encounter_id: int, session: Session = Depends(get_session)):
    if not db.delete_encounter(session, encounter_id):
        raise HTTPException(status_code=404, detail="Encounter not found")


@router.get("/{encounter_id}/participants")
def get_participants(encounter_id: int, session: Session = Depends(get_session)):
    if not db.get_encounter(session, encounter_id):
        raise HTTPException(status_code=404, detail="Encounter not found")
    return db.get_participants(session, encounter_id)


@router.post("/{encounter_id}/participants", status_code=201)
def add_participant(
    encounter_id: int, data: dict, session: Session = Depends(get_session)
):
    if not db.get_encounter(session, encounter_id):
        raise HTTPException(status_code=404, detail="Encounter not found")
    return db.add_participant(session, encounter_id, data)


@router.delete("/{encounter_id}/participants/{participant_id}", status_code=204)
def remove_participant(
    encounter_id: int,
    participant_id: int,
    session: Session = Depends(get_session),
):
    if not db.remove_participant(session, participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")
