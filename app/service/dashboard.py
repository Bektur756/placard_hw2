import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import EventRepo
from app.exception.event import EventNotFound
from app.schemas import EventDashboard


async def event_dashboard_service(event_id: int, organizer_id: int, db: AsyncSession) -> EventDashboard:
    event_repo = EventRepo(db)
    event = await event_repo.get_event_by_id_organizer_id(event_id, organizer_id)
    if not event:
        raise EventNotFound(event_id)

    sales_dashboard, occupancy_dashboard = await asyncio.gather(
        event_repo.get_sales_dashboard(event_id),
        event_repo.get_occupancy_dashboard(event_id),
    )

    return EventDashboard(
        event_title=event.title,
        starts_at=event.starts_at,
        sales=sales_dashboard,
        occupancy=occupancy_dashboard,
    )
