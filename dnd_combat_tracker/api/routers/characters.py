import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from dnd_combat_tracker.backends import get_backend
from dnd_combat_tracker.db import characters as db
from dnd_combat_tracker.db.engine import get_session

router = APIRouter(prefix="/characters", tags=["characters"])

_PARSE_PROMPT = """Extract the D&D character stats from this character sheet and return ONLY a JSON object with exactly these fields (use null for anything not found):
{
  "name": "Character Name",
  "player_name": null,
  "character_class": "Fighter",
  "subclass": null,
  "level": 1,
  "race": null,
  "max_hp": 10,
  "current_hp": 10,
  "temp_hp": 0,
  "ac": 10,
  "initiative_bonus": 0,
  "speed": 30,
  "strength": 10,
  "dexterity": 10,
  "constitution": 10,
  "intelligence": 10,
  "wisdom": 10,
  "charisma": 10,
  "passive_perception": 10,
  "notes": null
}
initiative_bonus is the DEX modifier plus any bonus (shown as the initiative modifier on the sheet).
Return ONLY the JSON object, no markdown, no explanation."""


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


@router.post("/import/pdf")
async def import_character_from_pdf(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Parse a D&D character sheet PDF using the configured AI backend."""
    try:
        backend = get_backend(session)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    content = await file.read()

    try:
        text = backend.parse_document(content, _PARSE_PROMPT)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI parsing failed: {exc}")

    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1].lstrip("json").strip() if len(parts) > 1 else text

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Could not parse character data from PDF")

    return data
