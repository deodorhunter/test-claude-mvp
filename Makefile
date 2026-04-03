.PHONY: up down logs migrate test shell-api shell-postgres verify-docs benchmark-session benchmark-report

COMPOSE = docker compose -f infra/docker-compose.yml --env-file .env

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

test:
	$(COMPOSE) exec api pytest -q --tb=short

migrate:
	$(COMPOSE) exec api alembic upgrade head

shell-api:
	$(COMPOSE) exec api bash

shell-postgres:
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-aiplatform} $${POSTGRES_DB:-aiplatform}

verify-docs:
	@bash benchmark/verify-docs.sh

benchmark-session:
	@mkdir -p benchmark/session-metrics
	@bash benchmark/capture-session-metrics.sh

benchmark-report:
	@bash benchmark/report-session-costs.sh
