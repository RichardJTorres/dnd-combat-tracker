# D&D Combat Tracker

A local-first D&D 5.5e combat tracker with a FastAPI backend, SQLite database, and React frontend.

## Features

- **Bestiary** — bookmark creatures with full stat blocks; import directly from the D&D 5e SRD API (334 monsters)
- **Party** — manage your player characters with HP, AC, ability scores, and initiative bonuses
- **Encounters** — build encounters by combining bookmarked creatures and party members
- **Combat** — initiative tracker with HP bars, condition tracking, and turn management
- **AI backends** — pluggable LLM provider support (Claude, Gemini, OpenAI, Ollama) ready for future AI features

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLModel, SQLite |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| AI | Anthropic Claude, Google Gemini, OpenAI, Ollama |
| Testing | pytest (TDD — tests written before implementation) |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Install

```bash
make install
```

This creates a `.venv` Python virtual environment and installs all Python and npm dependencies.

### Run

```bash
make dev
```

- API server: http://localhost:8000
- Frontend dev server: http://localhost:5173

### Run tests

```bash
make test
```

## Configuration

Copy `.env.example` to `.env` and set any API keys you want to use:

```env
# Optional — only needed for AI features
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
OPENAI_API_KEY=sk-...

# Ollama (local) — defaults to http://localhost:11434
OLLAMA_HOST=http://localhost:11434
```

The app runs fully without any API keys — they are only required for AI features.

## Project Structure

```
dnd-combat-tracker/
├── dnd_combat_tracker/       # Python backend package
│   ├── config.py             # Settings (pydantic-settings, reads .env)
│   ├── dnd_api.py            # D&D 5e SRD API client + mapper
│   ├── backends/             # Pluggable LLM backends
│   │   ├── base.py           # BaseBackend ABC
│   │   ├── claude.py         # Anthropic Claude
│   │   ├── gemini.py         # Google Gemini
│   │   ├── openai.py         # OpenAI / ChatGPT
│   │   └── ollama.py         # Ollama (local)
│   ├── db/                   # Database layer
│   │   ├── models.py         # SQLModel table definitions
│   │   ├── engine.py         # SQLite engine + session
│   │   ├── creatures.py      # Creature CRUD
│   │   ├── characters.py     # Player character CRUD
│   │   ├── encounters.py     # Encounter + participant CRUD
│   │   ├── combat.py         # Combat session + combatant CRUD
│   │   └── settings.py       # Key/value settings CRUD
│   └── api/routers/          # FastAPI route handlers
│       ├── creatures.py      # /api/creatures
│       ├── characters.py     # /api/characters
│       ├── encounters.py     # /api/encounters
│       ├── combat.py         # /api/combat
│       ├── dnd_api.py        # /api/dnd (SRD import)
│       └── settings.py       # /api/settings (AI provider config)
├── tests/                    # pytest test suite
│   ├── conftest.py           # Shared fixtures (in-memory SQLite)
│   ├── test_db_*.py          # Database layer tests
│   ├── test_api_*.py         # HTTP endpoint tests
│   ├── test_backends.py      # AI backend tests
│   └── test_dnd_api.py       # D&D API mapper tests
└── web/                      # React frontend
    └── src/pages/
        ├── Bestiary.tsx      # Creature browser + SRD import
        ├── Party.tsx         # Player character management
        ├── Encounters.tsx    # Encounter builder
        ├── Combat.tsx        # Active combat tracker
        └── Settings.tsx      # AI provider configuration
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/creatures` | List bookmarked creatures (filterable) |
| POST | `/api/creatures` | Create a creature |
| GET/PATCH/DELETE | `/api/creatures/{id}` | Get, update, or delete a creature |
| GET | `/api/dnd/monsters?search=` | Search D&D SRD API |
| POST | `/api/dnd/monsters/{index}/import` | Import a monster to local bestiary |
| GET | `/api/characters` | List player characters |
| POST | `/api/characters` | Create a character |
| GET | `/api/encounters` | List encounters |
| POST | `/api/encounters` | Create an encounter |
| POST | `/api/encounters/{id}/participants` | Add a creature/character to encounter |
| POST | `/api/combat/sessions` | Start a combat session |
| POST | `/api/combat/sessions/{id}/next-turn` | Advance initiative |
| PATCH | `/api/combat/combatants/{id}` | Update HP, conditions, etc. |
| GET | `/api/settings` | Get active AI provider/model |
| PUT | `/api/settings` | Set AI provider/model |
| GET | `/api/settings/providers` | List providers with configuration status |
| GET | `/api/settings/providers/{id}/models` | List available models for a provider |
