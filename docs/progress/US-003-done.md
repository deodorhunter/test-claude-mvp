# US-003: Docker Compose Local Environment — Done

## Summary
Created Docker Compose local dev stack with all 6 services on the `ai-platform` Docker network.

## Services

| Service | Image | Exposed Port | Notes |
|---|---|---|---|
| postgres | postgres:16-alpine | internal | health: pg_isready |
| redis | redis:7-alpine | internal | AOF persistence enabled |
| qdrant | qdrant/qdrant:v1.9.2 | internal (6333) | vector DB for RAG |
| api | local build | 8000 | FastAPI backend |
| plone | plone/plone-backend:6.0.12 | 8080 | Plone 6 REST API |
| volto | plone/plone-frontend:18.0.0 | 3000 | React/Volto frontend |

## Plone Version Note
Using `plone/plone-backend:6.0.12` which includes `plone.restapi` with JWT auth support.
The platform auth bridge (US-004) depends on:
- `POST /@login` — returns `{"token": "..."}`
- `GET /@users/{username}` — returns user info including roles

Verify after `make up`:
```bash
curl -s -X POST http://localhost:8080/Plone/@login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"admin"}' | python3 -m json.tool
```

## Secrets
All secrets via `.env` file (gitignored). `POSTGRES_PASSWORD` is required — compose
fails with a clear error if not set. `.env.example` updated with Docker variables.

## Make Targets
- `make up` — build images and start all services detached
- `make down` — stop and remove containers
- `make logs` — tail all service logs
- `make migrate` — run `alembic upgrade head` inside api container
- `make shell-api` — interactive bash in api container
- `make shell-postgres` — psql shell in postgres container

## Network
All services share the `ai-platform` bridge network. The `api` container resolves
`http://plone:8080` via Docker DNS — this is the URL configured as `PLONE_BASE_URL`.
