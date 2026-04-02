"""AI monster generation endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.backends import get_backend
from dnd_combat_tracker.ai_generator import generate_monster, MonsterGenerationError

router = APIRouter(prefix="/ai", tags=["ai"])


class GenerateRequest(BaseModel):
    prompt: str


@router.post("/generate-monster")
def generate_monster_endpoint(
    body: GenerateRequest,
    session: Session = Depends(get_session),
):
    """
    Generate a D&D monster stat block from a natural-language description.
    Returns a creature field dict suitable for preview — does NOT save to DB.
    """
    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    try:
        backend = get_backend(session)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    try:
        return generate_monster(backend, body.prompt)
    except MonsterGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
