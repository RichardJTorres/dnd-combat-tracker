from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db import creatures as db

router = APIRouter(prefix="/creatures", tags=["creatures"])


@router.get("")
def list_creatures(
    search: Optional[str] = None,
    creature_type: Optional[str] = None,
    session: Session = Depends(get_session),
):
    return db.list_creatures(session, search=search, creature_type=creature_type)


@router.post("", status_code=201)
def create_creature(data: dict, session: Session = Depends(get_session)):
    return db.create_creature(session, data)


@router.get("/{creature_id}")
def get_creature(creature_id: int, session: Session = Depends(get_session)):
    creature = db.get_creature(session, creature_id)
    if not creature:
        raise HTTPException(status_code=404, detail="Creature not found")
    return creature


@router.patch("/{creature_id}")
def update_creature(
    creature_id: int, data: dict, session: Session = Depends(get_session)
):
    creature = db.update_creature(session, creature_id, data)
    if not creature:
        raise HTTPException(status_code=404, detail="Creature not found")
    return creature


@router.delete("/{creature_id}", status_code=204)
def delete_creature(creature_id: int, session: Session = Depends(get_session)):
    if not db.delete_creature(session, creature_id):
        raise HTTPException(status_code=404, detail="Creature not found")
