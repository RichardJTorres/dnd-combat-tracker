from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db import combat as db
from dnd_combat_tracker.db import encounters as enc_db

router = APIRouter(prefix="/combat", tags=["combat"])


@router.post("/sessions", status_code=201)
def start_combat(data: dict, session: Session = Depends(get_session)):
    """
    Start a new combat session.
    Body: { encounter_id: int, combatants: [{name, combatant_type, initiative, max_hp, current_hp, ac, ...}] }
    """
    encounter_id = data.get("encounter_id")
    if not encounter_id or not enc_db.get_encounter(session, encounter_id):
        raise HTTPException(status_code=404, detail="Encounter not found")
    combatants_data = data.get("combatants", [])
    combat = db.start_combat(session, encounter_id, combatants_data)
    return {
        "session": combat,
        "combatants": db.get_combatants(session, combat.id),
    }


@router.get("/sessions/{session_id}")
def get_combat_session(session_id: int, session: Session = Depends(get_session)):
    combat = db.get_combat_session(session, session_id)
    if not combat:
        raise HTTPException(status_code=404, detail="Combat session not found")
    return {
        "session": combat,
        "combatants": db.get_combatants(session, session_id),
    }


@router.get("/sessions/{session_id}/active")
def get_active_combat(session_id: int, session: Session = Depends(get_session)):
    """Get the current active combat state."""
    combat = db.get_combat_session(session, session_id)
    if not combat:
        raise HTTPException(status_code=404, detail="Combat session not found")
    return {
        "session": combat,
        "combatants": db.get_combatants(session, session_id),
        "active_combatants": db.get_active_combatants(session, session_id),
    }


@router.post("/sessions/{session_id}/next-turn")
def next_turn(session_id: int, session: Session = Depends(get_session)):
    combat = db.next_turn(session, session_id)
    if not combat:
        raise HTTPException(status_code=404, detail="Combat session not found or inactive")
    return {
        "session": combat,
        "combatants": db.get_combatants(session, session_id),
    }


@router.post("/sessions/{session_id}/end")
def end_combat(session_id: int, session: Session = Depends(get_session)):
    combat = db.end_combat(session, session_id)
    if not combat:
        raise HTTPException(status_code=404, detail="Combat session not found")
    return combat


@router.patch("/combatants/{combatant_id}")
def update_combatant(
    combatant_id: int, data: dict, session: Session = Depends(get_session)
):
    combatant = db.update_combatant(session, combatant_id, data)
    if not combatant:
        raise HTTPException(status_code=404, detail="Combatant not found")
    return combatant
