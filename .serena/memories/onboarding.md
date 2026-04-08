# test-claude-mvp
Multi-tenant AI orchestration platform. EU AI Act compliant.
Backend: FastAPI/SQLAlchemy/Alembic (Python 3.11), PostgreSQL, Redis
AI: Ollama local + Claude API, LiteLLM proxy, Qdrant RAG
CMS: Plone 6 + Volto (TypeScript/React)
Structure: backend/ ai/ frontend/ infra/ .claude/ docs/
Entry: backend/app/main.py | AI: ai/models/base.py