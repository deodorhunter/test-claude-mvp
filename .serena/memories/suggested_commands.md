# Key Commands
Tests: docker exec -e PYTHONPATH=/app ai-platform-api pytest -q --tb=short
Migrate: docker exec ai-platform-api alembic upgrade head 2>&1 | tail -5
Start platform: docker compose -f infra/docker-compose.yml up -d
Start AI tools: docker compose -f infra/docker-compose.ai-tools.yml up -d
Benchmark: bash benchmark/measure-context-size.sh