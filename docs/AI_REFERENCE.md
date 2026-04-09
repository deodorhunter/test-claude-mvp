# AI_REF v2 — rule-004: memories first; read here ONLY for env/health/mounts
# Notation: svc:port→health-path(expected) | K:V(type)[default] | (ai-tools)=docker-compose.ai-tools.yml

## SVCS
api:8000→/health(200) | pg:5432→pg_isready | redis:6379→PING | qdrant:6333→/healthz(200) | ollama:11434→/api/tags(JSON) | litellm:4000(ai-tools) | serena-mcp:9121(ai-tools) | plone:8080→/@@ok | plone-mcp:9120→/sse(SSE) | volto:3000

## MAKE
up:compose-up-d-build | down:compose-down | logs:compose-logs-f | migrate:exec-api-alembic-upgrade | shell-api | shell-pg

## PATHS
core:backend/app/main.py,backend/app/config.py,backend/app/db/models.py | migrations:backend/alembic/versions/ | auth:backend/app/auth/ | routes:backend/app/api/ | infra:infra/docker-compose.yml,.env.example,infra/docker/Dockerfile.backend | ai:ai/,ai/planner/planner.py,ai/models/,ai/mcp/registry.py,ai/mcp/servers/plone.py | mcp-node:infra/plone-mcp/src/index.ts | plugins:plugins/

## ENV
DATABASE_URL(pg+asyncpg://) | REDIS_URL | SECRET_KEY(JWT) | PLONE_BASE_URL | QDRANT_URL | CORS_ORIGINS(JSON-arr) | ENVIRONMENT(dev|prod) | ACCESS_TOKEN_EXPIRE_MINUTES[60] | REFRESH_TOKEN_EXPIRE_DAYS[7] | AI_MODE(demo|prod) | OLLAMA_URL | OLLAMA_MODEL | ANTHROPIC_BASE_URL[LiteLLM:localhost:4000] | CONTEXT7_API_KEY | NAVIGATION_BACKEND[serena](serena|cbm|both,.claude/settings.json,docs/NAVIGATION_BACKENDS.md) | POSTGRES_DB | POSTGRES_USER | POSTGRES_PASSWORD | PLONE_USERNAME | PLONE_PASSWORD | PLONE_MCP_URL

## MOUNTS
../plugins/→/app/plugins/ | ../ai/→/app/ai/ | backend/→/app/ | vols:postgres_data,redis_data,qdrant_data,ollama_data

## MCP
context7:stdio-npx(cloud,rule-011,lib-names+queries-only) | serena:SSE-localhost:9121(py+ts,config:infra/serena_config.json,ignored:.git/node_modules/__pycache__/.venv/,requires:make-up-ai-tools)
