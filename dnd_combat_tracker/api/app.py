from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from dnd_combat_tracker.db.engine import init_db
from dnd_combat_tracker.api.routers import status, creatures, characters, encounters, combat, dnd_api, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="D&D Combat Tracker", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router, prefix="/api")
app.include_router(creatures.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(encounters.router, prefix="/api")
app.include_router(combat.router, prefix="/api")
app.include_router(dnd_api.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

# Serve the built React frontend in production
_dist = os.path.join(os.path.dirname(__file__), "..", "..", "web", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
