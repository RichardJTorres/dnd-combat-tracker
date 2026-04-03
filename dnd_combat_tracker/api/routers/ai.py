"""AI monster generation endpoints."""

import base64

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db.models import Creature
from dnd_combat_tracker.backends import get_backend, get_image_backend
from dnd_combat_tracker.ai_generator import generate_monster, generate_monster_art, MonsterGenerationError, VALID_CRS

router = APIRouter(prefix="/ai", tags=["ai"])


class GenerateRequest(BaseModel):
    prompt: str
    cr: float

    @field_validator("cr")
    @classmethod
    def cr_must_be_valid(cls, v: float) -> float:
        if v not in VALID_CRS:
            raise ValueError(
                f"cr must be one of: 0, 1/8, 1/4, 1/2, or 1–30. Got {v!r}."
            )
        return v


@router.post("/generate-monster")
def generate_monster_endpoint(
    body: GenerateRequest,
    session: Session = Depends(get_session),
):
    """
    Generate a D&D monster stat block from a description and an explicit CR.
    Returns a creature field dict suitable for preview — does NOT save to DB.
    """
    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    try:
        backend = get_backend(session)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    try:
        return generate_monster(backend, body.prompt, cr=body.cr)
    except MonsterGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


class ArtRequest(BaseModel):
    creature_id: int


@router.post("/generate-monster-art")
def generate_monster_art_endpoint(
    body: ArtRequest,
    session: Session = Depends(get_session),
):
    """
    Generate grimdark art for an existing creature and persist it.
    Returns { "art_data": "<base64 PNG>" }.
    """
    creature = session.exec(select(Creature).where(Creature.id == body.creature_id)).first()
    if creature is None:
        raise HTTPException(status_code=404, detail="Creature not found")

    try:
        image_backend = get_image_backend(session)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    try:
        png_bytes = generate_monster_art(image_backend, creature)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}")

    creature.art_data = base64.b64encode(png_bytes).decode()
    session.add(creature)
    session.commit()

    return {"art_data": creature.art_data}
