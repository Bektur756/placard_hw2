from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus, Event, EventSeat, Seat, SeatStatus


class BaseRepo:
    def __init__(self, session: AsyncSession):
        self.session = session


class BookingRepo(BaseRepo):
    async def get_by_user_id_event_id(
        self,
        user_id: int,
        event_id: int,
    ) -> list[Booking]:
        query = select(Booking).where(
            Booking.user_id == user_id,
            Booking.event_id == event_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_pending(
        self,
        event_id: int,
        user_id: int,
        amount: int,
        reserved_until: datetime,
    ) -> Booking:
        booking = Booking(
            event_id=event_id,
            user_id=user_id,
            amount=amount,
            payment_commission=0,
            protection_price=None,
            with_protection=False,
            status=BookingStatus.pending_payment,
            reserved_until=reserved_until,
        )
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def apply_quotes(
        self,
        booking: Booking,
        payment_commission: int,
        protection_price: int | None,
    ) -> None:
        booking.payment_commission = payment_commission
        booking.protection_price = protection_price


class EventRepo(BaseRepo):
    async def get_by_id(self, event_id: int) -> Event | None:
        query = select(Event).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_event_seats(
        self,
        event_id: int,
        seat_ids: list[int],
        now: datetime,
    ) -> list[tuple[EventSeat, Seat]]:
        query = (
            select(EventSeat, Seat)
            .join(Seat, Seat.id == EventSeat.seat_id)
            .where(
                EventSeat.event_id == event_id,
                EventSeat.seat_id.in_(seat_ids),
                or_(
                    EventSeat.status == SeatStatus.available,
                    and_(
                        EventSeat.status == SeatStatus.reserved,
                        EventSeat.reserved_until < now,
                    ),
                ),
            )
            .with_for_update(of=EventSeat, skip_locked=True)
        )

        result = await self.session.execute(query)
        return [(event_seat, seat) for event_seat, seat in result.all()]

    async def reserve_event_seats(
        self,
        seat_rows: list[tuple[EventSeat, Seat]],
        booking_id: int,
        reserved_until: datetime,
    ) -> None:
        for event_seat, _ in seat_rows:
            event_seat.status = SeatStatus.reserved
            event_seat.reserved_until = reserved_until
            event_seat.booking_id = booking_id
