from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from ..config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_async_engine(settings.DATABASE_URL, echo=False)


def get_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency for DB sessions."""
    engine = get_engine()
    factory = get_session_factory(engine)
    async with factory() as session:
        yield session
