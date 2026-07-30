import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import engine
from app.database.repository import EventRepo
from app.exception.event import EventNotFound
from app.schemas import EventDashboard, OccupancyDashboard, SalesDashboard


async def event_dashboard_service(event_id: int, organizer_id: int, db: AsyncSession) -> EventDashboard:
    event_repo = EventRepo(db)
    event = await event_repo.get_event_by_id_organizer_id(event_id, organizer_id)
    if not event:
        raise EventNotFound(event_id)

    sales_dashboard, occupancy_dashboard = await asyncio.gather(
        load_sales_dashboard(event_id),
        load_occupancy_dashboard(event_id),
    )

    return EventDashboard(
        event_title=event.title,
        starts_at=event.starts_at,
        sales=sales_dashboard,
        occupancy=occupancy_dashboard,
    )


async def load_sales_dashboard(event_id: int) -> SalesDashboard:
    async with AsyncSession(engine, expire_on_commit=False) as db:
        return await EventRepo(db).get_sales_dashboard(event_id)


async def load_occupancy_dashboard(event_id: int) -> OccupancyDashboard:
    async with AsyncSession(engine, expire_on_commit=False) as db:
        return await EventRepo(db).get_occupancy_dashboard(event_id)
