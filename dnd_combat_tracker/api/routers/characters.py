from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db import characters as db

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("")
def list_characters(session: Session = Depends(get_session)):
    return db.list_characters(session)


@router.post("", status_code=201)
def create_character(data: dict, session: Session = Depends(get_session)):
    return db.create_character(session, data)


@router.get("/{character_id}")
def get_character(character_id: int, session: Session = Depends(get_session)):
    character = db.get_character(session, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.patch("/{character_id}")
def update_character(
    character_id: int, data: dict, session: Session = Depends(get_session)
):
    character = db.update_character(session, character_id, data)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.delete("/{character_id}", status_code=204)
def delete_character(character_id: int, session: Session = Depends(get_session)):
    if not db.delete_character(session, character_id):
        raise HTTPException(status_code=404, detail="Character not found")
