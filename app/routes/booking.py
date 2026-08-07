from fastapi import APIRouter
from app.routes.dependency import CurrentUserId
from app.schemas import PaymentCreate, PaymentCompleted


router = APIRouter()


@router.post("/bookings/{booking_id}/pay")
async def pay_booking(
    booking_id: int,
    payload: PaymentCreate,
    user_id: CurrentUserId,
) -> PaymentCompleted:
    """Принимает способ оплаты и флаг with_protection."""
    ...