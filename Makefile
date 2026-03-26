.PHONY: up down logs migrate shell-api shell-postgres

up:
	docker compose -f infra/docker-compose.yml up -d --build

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

migrate:
	docker compose -f infra/docker-compose.yml exec api alembic upgrade head

shell-api:
	docker compose -f infra/docker-compose.yml exec api bash

shell-postgres:
	docker compose -f infra/docker-compose.yml exec postgres psql -U $${POSTGRES_USER:-aiplatform} $${POSTGRES_DB:-aiplatform}
