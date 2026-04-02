.PHONY: install dev api web test fmt

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

web/node_modules:
	cd web && npm install --silent

install: $(VENV)/bin/activate web/node_modules

dev: install
	@trap 'kill 0' SIGINT; \
	$(VENV)/bin/dnd-combat-tracker & \
	cd web && npm run dev & \
	wait

api: install
	$(VENV)/bin/dnd-combat-tracker

web: web/node_modules
	cd web && npm run dev

test: $(VENV)/bin/activate
	$(PYTHON) -m pytest tests/ -v

fmt: $(VENV)/bin/activate
	$(VENV)/bin/black dnd_combat_tracker/ tests/
