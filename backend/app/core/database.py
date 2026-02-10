from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_db_url = settings.database_url or "sqlite+aiosqlite:///:memory:"

# Pool settings only apply to connection-pooled databases (not SQLite)
_engine_kwargs: dict = {"echo": settings.debug}
if not _db_url.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_s,
        pool_pre_ping=True,
    )

engine = create_async_engine(_db_url, **_engine_kwargs)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def verify_database_connection() -> bool:
    """
    Verify database connectivity on startup.

    Returns:
        True if connection successful

    Raises:
        RuntimeError: If connection fails
    """
    try:
        async with async_session_factory() as session:
            # Simple query to verify connection
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        # Mask password in error message
        masked_url = _db_url.split("@")[0].split("://")[0] + "://[REDACTED]@"
        if "@" in _db_url:
            masked_url += _db_url.split("@")[1]
        raise RuntimeError(
            f"Database connection failed: {str(e)}\n"
            f"Ensure PostgreSQL is running and DATABASE_URL is correct.\n"
            f"Current DATABASE_URL: {masked_url}"
        ) from e
