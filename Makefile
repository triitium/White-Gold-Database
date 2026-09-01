SHELL := /bin/bash
COMPOSE := podman compose --env-file deployment/local/.env

.PHONY: dev-up dev-down dev-logs dev-migrate backend-test backend-compile

dev-up:
	$(COMPOSE) up --build -d

dev-down:
	$(COMPOSE) down

dev-logs:
	$(COMPOSE) logs -f

dev-migrate:
	$(COMPOSE) exec backend alembic upgrade head

backend-test:
	cd backend && PYTHONPATH=. pytest -q

backend-compile:
	python -m compileall -q backend/app backend/scripts
