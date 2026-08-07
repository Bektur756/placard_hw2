from datetime import datetime

from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus, Event, EventSeat, EventView, Seat, SeatStatus
from app.schemas import OccupancyDashboard, SalesDashboard


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

        await self.session.flush()

    async def get_event_by_id_organizer_id(self, event_id: int, organizer_id: int) -> Event | None:
        query = (
            select(Event)
            .where(Event.id == event_id, Event.organizer_id == organizer_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_event_by_id(self, event_id: int) -> Event | None:
        query = (
            select(Event)
            .where(Event.id == event_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_event_views(self, event_counts: dict[int, int]) -> None:
        if not event_counts:
            return

        values = [
            {
                "event_id": event_id,
                "views_count": views_count,
            }
            for event_id, views_count in event_counts.items()
        ]
        query = insert(EventView).values(values)
        query = query.on_conflict_do_update(
            index_elements=[EventView.event_id],
            set_={
                "views_count": EventView.views_count + query.excluded.views_count,
            },
        )
        await self.session.execute(query)

    async def get_sales_dashboard(self, event_id: int) -> SalesDashboard:
        query = (
            select(
                func.count(distinct(EventSeat.booking_id)).filter(
                    EventSeat.status == SeatStatus.sold,
                    EventSeat.booking_id.is_not(None),
                ),
                func.count(EventSeat.id).filter(EventSeat.status == SeatStatus.sold),
                func.coalesce(
                    func.sum(EventSeat.price).filter(EventSeat.status == SeatStatus.sold),
                    0,
                ),
            )
            .where(EventSeat.event_id == event_id)
        )

        result = await self.session.execute(query)
        paid_orders, sold_tickets, revenue = result.one()
        average_order = revenue // paid_orders if paid_orders else 0

        return SalesDashboard(
            paid_orders=paid_orders,
            sold_tickets=sold_tickets,
            revenue=revenue,
            average_order=average_order,
        )

    async def get_occupancy_dashboard(
        self,
        event_id: int,
    ) -> OccupancyDashboard:
        now = datetime.now()
        query = (
            select(
                func.count(EventSeat.id),
                func.count(EventSeat.id).filter(
                    or_(
                        EventSeat.status == SeatStatus.available,
                        and_(
                            EventSeat.status == SeatStatus.reserved,
                            EventSeat.reserved_until <= now,
                        ),
                    ),
                ),
                func.count(EventSeat.id).filter(
                    EventSeat.status == SeatStatus.reserved,
                    EventSeat.reserved_until > now,
                ),
                func.count(EventSeat.id).filter(EventSeat.status == SeatStatus.sold),
            )
            .where(EventSeat.event_id == event_id)
        )

        result = await self.session.execute(query)
        total, available, reserved, sold = result.one()
        occupancy_percent = round(((reserved + sold) / total) * 100, 2) if total else 0

        return OccupancyDashboard(
            total=total,
            available=available,
            reserved=reserved,
            sold=sold,
            occupancy_percent=occupancy_percent,
        )
