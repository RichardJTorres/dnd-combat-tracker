# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install    # Create .venv and install all Python + npm dependencies
make dev        # Run API (port 8000) and frontend dev server (port 5173) in parallel
make api        # Run FastAPI server only
make web        # Run Vite dev server only
make test       # Run pytest suite
make fmt        # Format Python with black
```

Run a single test file:
```bash
.venv/bin/pytest tests/test_ai_generator.py -v
```

Run a single test by name:
```bash
.venv/bin/pytest tests/test_ai_generator.py::test_cr_validation -v
```

## Architecture

**Stack**: FastAPI + SQLModel (SQLite) backend, React 18 + TypeScript + Vite + Tailwind frontend.

### Backend structure

`dnd_combat_tracker/` is the Python package:
- `config.py` — Pydantic-settings; reads `.env` for `DATABASE_URL`, `PORT`, and AI API keys
- `ai_generator.py` — AI monster generation with DMG 2024 balance enforcement
- `dnd_api.py` — D&D 5e SRD API client and response mapper
- `backends/` — Pluggable LLM backends (Claude, Gemini, OpenAI, Ollama) behind a `BaseBackend` ABC; `get_backend(session)` factory selects the active provider from DB settings
- `db/` — SQLite engine, SQLModel table definitions in `models.py`, and per-entity CRUD modules
- `api/routers/` — FastAPI routers, one per domain (`creatures`, `characters`, `encounters`, `combat`, `dnd_api`, `settings`, `ai`)

### Frontend structure

`web/src/pages/` has one component per page:
- `Bestiary.tsx` — creature browser with AI generation panel and SRD import
- `Party.tsx` — player character management
- `Encounters.tsx` — encounter builder
- `Combat.tsx` — initiative tracker with HP and condition tracking
- `Settings.tsx` — AI provider/model selection

Vite proxies `/api/*` to `localhost:8000` during development.

### AI monster generation

`POST /api/ai/generate-monster` accepts `{prompt, cr}`. The CR must be a value from the `VALID_CRS` frozenset (returns 422 otherwise). `ai_generator.py` injects DMG 2024 balance targets (AC, HP range, attack bonus, damage per round, save DC) from the `_CR_TARGETS` lookup table into every LLM request. `_normalise()` unconditionally forces the returned JSON's `cr` field to match the requested value so the LLM cannot drift. The endpoint returns a preview dict — it does **not** save to the DB.

### Database

JSON-valued fields on models (traits, actions, skills, etc.) are stored as JSON strings because SQLite has no native JSON type. Tests use in-memory SQLite via the `session` fixture in `conftest.py`.

### Settings / provider config

Active AI provider, model names, and API keys are stored in the `AppSetting` key/value table (managed via `/api/settings`). `get_backend(session)` reads these at request time.
