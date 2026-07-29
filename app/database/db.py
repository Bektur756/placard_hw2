from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.config.setting import DATABASE_URL


engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
