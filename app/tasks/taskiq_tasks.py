from datetime import datetime, timedelta
from typing import Any

from app.config.httpx_client import protection_client

from app.database.db import database
from app.schemas import EventDashboard
from app.service.booking import BookingService
from app.service.protection import ProtectionService
from app.service.report import ReportService
from app.tasks.taskiq_app import broker_cpu, broker_async


@broker_cpu.task(
    task_name="generate_report",
    max_retries=2,
    retry_on_error=True,
)
def generate_report(
    dashboard: EventDashboard | dict[str, Any],
) -> None:
    ReportService().generate_event_dashboard_report(dashboard)


@broker_async.task(
    task_name="outdated_booking",
    schedule=[{
        "schedule_id": "outdated_booking",
        "interval": timedelta(minutes=1)
    }],
)
async def outdated_booking() -> None:
    async with database.session() as db:
        await BookingService(db).remove_outdated_bookings()


@broker_async.task(
    task_name="protection_attempt",
    max_retries=2,
    retry_on_error=True,
)
async def protection_attempt(
    booking_id: int,
    ticket_amount: int,
    event_category: str,
    event_starts_at: datetime | str,
) -> None:
    async with database.session() as db:
        service = ProtectionService(
            db=db,
            protection_client=protection_client,
        )
        await service.update_protection_price(
            booking_id=booking_id,
            ticket_amount=ticket_amount,
            event_category=event_category,
            event_starts_at=event_starts_at,
        )
