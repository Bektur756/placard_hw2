from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends, Header
from app.database.db import DatabaseManager, database
from app.service.checkout import CheckoutService
from app.service.dashboard import DashboardService


def get_current_user_id(x_user_id: Annotated[int, Header()]) -> int:
    return x_user_id


CurrentUserId = Annotated[int, Depends(get_current_user_id)]


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
