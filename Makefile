.PHONY: up down logs migrate shell-api shell-postgres

COMPOSE = docker compose -f infra/docker-compose.yml --env-file .env

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) exec api alembic upgrade head

shell-api:
	$(COMPOSE) exec api bash

shell-postgres:
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-aiplatform} $${POSTGRES_DB:-aiplatform}
