from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db_session
from app.routes.dependency import CurrentUserId
from app.schemas import EventCreate, EventRead, EventDashboard
from app.service.dashboard import event_dashboard_service

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
        db: AsyncSession = Depends(get_db_session),
) -> EventDashboard:
    """Возвращает аналитические данные для дашборда по мероприятию."""
    return await event_dashboard_service(event_id, organizer_id, db)
