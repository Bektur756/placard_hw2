from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db_session
from app.routes.dependency import CurrentUserId
from app.schemas import BookingCreate, CheckoutResponse, EventRead, EventSeatRead
from app.service.checkout import prepare_checkout_service

router = APIRouter()


@router.get("/events")
async def list_events() -> list[EventRead]:
    """Возвращает список мероприятий для клиента."""
    ...


@router.get("/events/{event_id}")
async def get_event(event_id: int) -> EventRead:
    """Возвращает описание мероприятия."""
    ...


@router.get("/events/{event_id}/seats")
async def list_event_seats(event_id: int) -> list[EventSeatRead]:
    """Возвращает места на мероприятии с ценами и статусами."""
    ...


@router.post("/events/{event_id}/checkout")
async def prepare_checkout(
    event_id: int,
    payload: BookingCreate,
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db_session),
) -> CheckoutResponse:
    """Временно бронирует места за клиентом, возвращает итоговую стоимость
    и возможность страховки."""

    return await prepare_checkout_service(
        event_id=event_id,
        seat_ids=payload.seat_ids,
        user_id=user_id,
        db=db,
    )
