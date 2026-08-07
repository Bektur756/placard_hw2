import asyncio
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.database.db import DatabaseManager
from app.schemas import CheckoutBooking, CheckoutResponse
from app.config.httpx_client import (
    payment_client,
    protection_client,
)


class CheckoutService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def prepare_checkout(
        self,
        event_id: int,
        seat_ids: list[int],
        user_id: int,
    ) -> CheckoutResponse:
        if len(seat_ids) != len(set(seat_ids)):
            raise HTTPException(status_code=400, detail="Seat ids must be unique")

        event = await self.db.events.get_by_id(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        now = datetime.now()
        seat_rows = await self.db.events.get_event_seats(
            event_id=event_id,
            seat_ids=seat_ids,
            now=now,
        )
        if len(seat_rows) != len(seat_ids):
            raise HTTPException(status_code=409, detail="Some seats are not available")

        ticket_amount = sum(event_seat.price for event_seat, _ in seat_rows)
        reserved_until = now + timedelta(minutes=15)

        booking = await self.db.bookings.create_pending(
            event.id,
            user_id,
            ticket_amount,
            reserved_until,
        )

        await self.db.events.reserve_event_seats(
            seat_rows,
            booking.id,
            reserved_until,
        )

        payment_result, protection_result = await asyncio.gather(
            payment_client.calculate(
                booking_id=booking.id,
                amount=ticket_amount,
            ),
            protection_client.calculate(
                booking_id=booking.id,
                ticket_amount=ticket_amount,
                event_category=event.category,
                event_starts_at=event.starts_at,
            ),
            return_exceptions=True,
        )

        if isinstance(payment_result, Exception):
            raise HTTPException(status_code=502, detail="Payment service unavailable")

        if isinstance(protection_result, Exception):
            protection_result = None

        await self.db.bookings.apply_quotes(
            booking,
            payment_result.commission,
            protection_result.price if protection_result else None,
        )

        response = CheckoutResponse(
            booking=CheckoutBooking(
                id=booking.id,
                event_title=event.title,
                starts_at=event.starts_at,
                seats=[
                    {
                        "id": seat.id,
                        "sector": seat.sector,
                        "row": seat.row,
                        "number": seat.number,
                        "price": event_seat.price,
                    }
                    for event_seat, seat in seat_rows
                ],
                base_amount=ticket_amount,
                payment_commission=booking.payment_commission,
                protection_price=booking.protection_price,
                with_protection=booking.with_protection,
                reserved_until=booking.reserved_until,
            ),
            payment=payment_result,
            protection=protection_result,
        )

        await self.db.commit()
        return response
