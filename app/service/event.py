from redis.asyncio import Redis
from app.database.db import DatabaseManager
from app.exception.event import EventNotFound
from app.schemas import EventRead


class EventService:
    def __init__(self, db: DatabaseManager, redis: Redis) -> None:
        self.db = db
        self.redis = redis

    async def get_event_by_id(self, event_id: int) -> EventRead:
        key = f"event_{event_id}"
        event = await self.redis.get(key)
        if event:
            return EventRead.model_validate_json(event)

        async with self.redis.lock(
            name=f"lock:get_event_{event_id}",
            timeout=5,
            blocking_timeout=3,
        ):
            event = await self.redis.get(key)
            if event:
                return EventRead.model_validate_json(event)

            event = await self.db.events.get_by_id(event_id)
            if not event:
                raise EventNotFound(event_id)

            event_read = EventRead.model_validate(event)
            await self.redis.set(key, event_read.model_dump_json(), ex=60)
            return event_read
