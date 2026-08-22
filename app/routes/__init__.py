from fastapi import APIRouter
from app.routes.booking import router as booking_router
from app.routes.event import router as event_router
from app.routes.location import router as location_router
from app.routes.organizer import router as organizer_router

router = APIRouter()
router.include_router(event_router)
router.include_router(location_router)
router.include_router(booking_router)
router.include_router(organizer_router)
