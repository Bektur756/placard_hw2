from fastapi import APIRouter
from app.routes.dependency import CheckoutServiceDep, CurrentUserId, EventServiceRep
from app.schemas import BookingCreate, CheckoutResponse, EventRead, EventSeatRead


router = APIRouter()


@router.get("/events")
async def list_events() -> list[EventRead]:
    """Возвращает список мероприятий для клиента."""
    ...


@router.get("/events/{event_id}")
async def get_event(
        event_id: int,
        service: EventServiceRep,
) -> EventRead:
    """Возвращает описание мероприятия."""
    return await service.get_event_by_id(event_id=event_id)


@router.get("/events/{event_id}/seats")
async def list_event_seats(event_id: int) -> list[EventSeatRead]:
    """Возвращает места на мероприятии с ценами и статусами."""
    ...


@router.post("/events/{event_id}/checkout")
async def prepare_checkout(
    event_id: int,
    payload: BookingCreate,
    user_id: CurrentUserId,
    service: CheckoutServiceDep,
) -> CheckoutResponse:
    """Временно бронирует места за клиентом, возвращает итоговую стоимость
    и возможность страховки."""
    return await service.prepare_checkout(
        event_id=event_id,
        seat_ids=payload.seat_ids,
        user_id=user_id,
    )
