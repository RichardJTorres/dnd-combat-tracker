"""Endpoints for browsing and importing monsters from the D&D 5e SRD API."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db import creatures as creature_db
from dnd_combat_tracker.db.models import Creature
import dnd_combat_tracker.dnd_api as api

router = APIRouter(prefix="/dnd", tags=["dnd-api"])


@router.get("/monsters")
def search_monsters(search: Optional[str] = None):
    """Search monsters from the D&D 5e SRD API. Returns name/index pairs."""
    try:
        results = api.search_monsters(search or "")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"D&D API unavailable: {exc}")
    return results


@router.post("/monsters/{index}/import", status_code=201)
def import_monster(index: str, session: Session = Depends(get_session)):
    """
    Import a monster from the D&D 5e SRD API into the local bestiary.
    If the monster was already imported (matched by name + source), returns 200.
    Returns the created or existing Creature.
    """
    # Fetch from external API
    try:
        data = api.fetch_monster(index)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"D&D API unavailable: {exc}")

    if data is None:
        raise HTTPException(status_code=404, detail=f"Monster '{index}' not found in D&D API")

    mapped = api.map_monster(data)

    # Deduplication: check if a creature with this name + source already exists
    existing = session.exec(
        select(Creature)
        .where(Creature.name == mapped["name"])
        .where(Creature.source == mapped["source"])
    ).first()

    if existing:
        from fastapi import Response
        import json

        # Return 200 with the existing creature; override default 201 status
        response = Response(
            content=existing.model_dump_json(),
            status_code=200,
            media_type="application/json",
        )
        return response

    creature = creature_db.create_creature(session, mapped)
    return creature
