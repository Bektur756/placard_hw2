from app.database.db import DatabaseManager


class BookingService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def remove_outdated_bookings(self):
        await self.db.bookings.remove_outdated_bookings()