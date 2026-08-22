from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.setting import DATABASE_URL
from app.database.repository import BookingRepo, EventRepo


engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


class Database:
    def __init__(
        self,
        engine: AsyncEngine,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> None:
        self._engine = engine
        self._session_maker = session_maker

    @asynccontextmanager
    async def session(self) -> AsyncGenerator["DatabaseManager", None]:
        async with self._session_maker() as session:
            db = DatabaseManager(session, self._session_maker)
            try:
                yield db
            except Exception:
                await db.rollback()
                raise

    async def close(self) -> None:
        await self._engine.dispose()


class DatabaseManager:
    def __init__(
        self,
        session: AsyncSession,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session = session
        self.session_maker = session_maker

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator["DatabaseManager", None]:
        async with self.session_maker() as new_session:
            db = DatabaseManager(new_session, self.session_maker)
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    @property
    def bookings(self) -> BookingRepo:
        return BookingRepo(self.session)

    @property
    def events(self) -> EventRepo:
        return EventRepo(self.session)


database = Database(engine, session_maker)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with database.session() as db:
        yield db.session
