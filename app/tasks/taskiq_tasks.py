from pathlib import Path

from app.config.httpx_client import protection_client
from app.pdf_report import generate_event_dashboard_pdf
from datetime import datetime, timedelta

from app.schemas import EventDashboard
from app.database.db import database
from app.tasks.taskiq_app import broker_cpu, broker_async


@broker_cpu.task(
    task_name="generate_report",
    max_retries=2,
    retry_on_error=True,
)
async def generate_report(
        event_title,
        starts_at,
        sales,
        occupancy,
):
    event_dashboard = EventDashboard.model_validate({
        "event_title": event_title,
        "starts_at": starts_at,
        "sales": sales,
        "occupancy": occupancy,
    })
    output_path = Path("reports") / f"{event_title}.pdf"
    generate_event_dashboard_pdf(
        event_dashboard,
        output_path,
        datetime.now()
    )


@broker_async.task(
    task_name="outdated_booking",
    schedule=[{
        "schedule_id": "outdated_booking",
        "interval": timedelta(minutes=1)
    }],
)
async def outdated_booking() -> None:
    async with database.session() as db:
        await db.bookings.remove_outdated_bookings()
        await db.commit()


@broker_async.task(
    task_name="protection_attempt",
    max_retries=2,
    retry_on_error=True,
)
async def protection_attempt(
        booking_id,
        ticket_amount,
        event_category,
        event_starts_at,
) -> None:
    if isinstance(event_starts_at, str):
        event_starts_at = datetime.fromisoformat(event_starts_at)

    protection_result = await protection_client.calculate(
        booking_id=booking_id,
        ticket_amount=ticket_amount,
        event_category=event_category,
        event_starts_at=event_starts_at,
    )
    if protection_result is None:
        raise RuntimeError("Protection API calculation failed")

    async with database.session() as db:
        await db.bookings.update_protection_price(
            booking_id=booking_id,
            protection_price=protection_result.price,
        )
        await db.commit()
