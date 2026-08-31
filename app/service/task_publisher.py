from datetime import datetime
from typing import Protocol

from app.schemas import EventDashboard


class TaskPublisher(Protocol):
    async def publish_report_generation(self, dashboard: EventDashboard) -> None:
        ...

    async def publish_protection_attempt(
        self,
        booking_id: int,
        ticket_amount: int,
        event_category: str,
        event_starts_at: datetime,
    ) -> None:
        ...
