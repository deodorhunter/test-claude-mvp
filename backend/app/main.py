from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .db.base import get_engine, get_session_factory
    from .audit.service import init_audit_service
    from .auth.token_store import init_redis
    import redis.asyncio as aioredis

    settings = get_settings()
    engine = get_engine()
    session_factory = get_session_factory(engine)
    init_audit_service(session_factory)

    # Initialize Redis client for refresh token JTI blacklist
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    init_redis(redis_client)

    logger.info("AI Orchestration Platform starting up")
    yield
    await redis_client.aclose()
    await engine.dispose()
    logger.info("AI Orchestration Platform shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Orchestration Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .api.v1.router import api_router
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
