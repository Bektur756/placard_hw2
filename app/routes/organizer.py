from fastapi import APIRouter
from app.routes.dependency import CurrentUserId, DashboardServiceDep
from app.schemas import EventCreate, EventRead, EventDashboard


router = APIRouter()


@router.get("/organizer/events")
async def list_organizer_events(organizer_id: CurrentUserId) -> list[EventRead]:
    """Возвращает список созданных событий текущего организатора."""
    ...


@router.post("/organizer/events")
async def create_event(payload: EventCreate, organizer_id: CurrentUserId) -> EventRead:
    """Создает мероприятие от лица текущего организатора."""
    ...


@router.get("/organizer/events/{event_id}/dashboard")
async def get_event_dashboard(
    event_id: int,
    organizer_id: CurrentUserId,
    service: DashboardServiceDep,
) -> EventDashboard:
    """Возвращает аналитические данные для дашборда по мероприятию."""
    return await service.get_event_dashboard(event_id, organizer_id)
