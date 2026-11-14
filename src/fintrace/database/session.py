from functools import lru_cache
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fintrace.core.config import Settings


@lru_cache
def get_engine():
    settings = Settings()

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache
def get_session_factory():
    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()

    try:
        yield session
    finally:
        session.close()