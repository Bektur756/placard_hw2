from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends, Header
from redis.asyncio import Redis

from app.config.redis_client import redis_service
from app.database.db import DatabaseManager, database
from app.lifespan_tasks.event_view_tracker import event_view_tracker
from app.service.checkout import CheckoutService
from app.service.dashboard import DashboardService
from app.service.event import EventService


def get_current_user_id(x_user_id: Annotated[int, Header()]) -> int:
    return x_user_id


CurrentUserId = Annotated[int, Depends(get_current_user_id)]


def get_redis() -> Redis:
    return redis_service.redis


async def get_db() -> AsyncGenerator[DatabaseManager, None]:
    async with database.session() as db:
        yield db


def get_checkout_service(
    db: Annotated[DatabaseManager, Depends(get_db)],
) -> CheckoutService:
    return CheckoutService(db=db)


CheckoutServiceDep = Annotated[CheckoutService, Depends(get_checkout_service)]


def get_dashboard_service(
    db: Annotated[DatabaseManager, Depends(get_db)],
) -> DashboardService:
    return DashboardService(db=db)


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


def get_event_service(
    db: Annotated[DatabaseManager, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> EventService:
    return EventService(
        db=db,
        redis=redis,
        event_view_tracker=event_view_tracker,
    )

EventServiceRep = Annotated[EventService, Depends(get_event_service)]
