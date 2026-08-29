from datetime import datetime
from app.config.httpx_client import ProtectionClient
from app.database.db import DatabaseManager


class ProtectionService:
    def __init__(
        self,
        db: DatabaseManager,
        protection_client: ProtectionClient,
    ) -> None:
        self.db = db
        self.protection_client = protection_client

    async def update_protection_price(
        self,
        booking_id: int,
        ticket_amount: int,
        event_category: str,
        event_starts_at: datetime | str,
    ) -> None:
        if isinstance(event_starts_at, str):
            event_starts_at = datetime.fromisoformat(event_starts_at)

        protection_result = await self.protection_client.calculate(
            booking_id=booking_id,
            ticket_amount=ticket_amount,
            event_category=event_category,
            event_starts_at=event_starts_at,
        )
        if protection_result is None:
            raise RuntimeError("Protection API calculation failed")

        await self.db.bookings.update_protection_price(
            booking_id=booking_id,
            protection_price=protection_result.price,
        )
        await self.db.commit()
