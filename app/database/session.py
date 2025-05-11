from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///db.sqlite3"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # CHANGE FOR PRODUCTION
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[Any, Any]:
    async with AsyncSessionLocal() as session:
        yield session
