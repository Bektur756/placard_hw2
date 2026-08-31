import asyncio

from app.database.db import DatabaseManager
from app.exception.event import EventNotFound
from app.schemas import EventDashboard, OccupancyDashboard, SalesDashboard
from app.service.task_publisher import TaskPublisher


class DashboardService:
    def __init__(self, db: DatabaseManager, task_publisher: TaskPublisher) -> None:
        self.db = db
        self.task_publisher = task_publisher

    async def get_event_dashboard(
        self,
        event_id: int,
        organizer_id: int,
    ) -> EventDashboard:
        event = await self.db.events.get_event_by_id_organizer_id(event_id, organizer_id)
        if not event:
            raise EventNotFound(event_id)

        sales_dashboard, occupancy_dashboard = await asyncio.gather(
            self._load_sales_dashboard(event_id),
            self._load_occupancy_dashboard(event_id),
        )

        dashboard = EventDashboard(
            event_title=event.title,
            starts_at=event.starts_at,
            sales=sales_dashboard,
            occupancy=occupancy_dashboard,
        )
        await self.task_publisher.publish_report_generation(dashboard)

        return dashboard

    async def _load_sales_dashboard(self, event_id: int) -> SalesDashboard:
        async with self.db.transaction() as db:
            return await db.events.get_sales_dashboard(event_id)

    async def _load_occupancy_dashboard(self, event_id: int) -> OccupancyDashboard:
        async with self.db.transaction() as db:
            return await db.events.get_occupancy_dashboard(event_id)
