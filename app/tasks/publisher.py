from datetime import datetime

from app.schemas import EventDashboard
from app.tasks.taskiq_tasks import generate_report, protection_attempt


class TaskiqTaskPublisher:
    async def publish_report_generation(self, dashboard: EventDashboard) -> None:
        await generate_report.kiq(dashboard=dashboard.model_dump(mode="json"))

    async def publish_protection_attempt(
        self,
        booking_id: int,
        ticket_amount: int,
        event_category: str,
        event_starts_at: datetime,
    ) -> None:
        await protection_attempt.kiq(
            booking_id=booking_id,
            ticket_amount=ticket_amount,
            event_category=event_category,
            event_starts_at=event_starts_at.isoformat(),
        )
