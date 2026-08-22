import random

from redis.asyncio import Redis
from app.database.db import DatabaseManager
from app.exception.event import EventNotFound
from app.lifespan_tasks.event_view_tracker import EventViewTracker
from app.schemas import EventRead

EVENT_CACHE_TTL_SECONDS = 60
EVENT_CACHE_TTL_JITTER_SECONDS = 15
EVENT_VIEW_DEDUP_TTL_SECONDS = 5 * 60


class EventService:
    def __init__(
        self,
        db: DatabaseManager,
        redis: Redis,
        event_view_tracker: EventViewTracker,
    ) -> None:
        self.db = db
        self.redis = redis
        self.event_view_tracker = event_view_tracker

    async def get_event_by_id(self, event_id: int, client_host: str | None) -> EventRead:
        key = f"event_{event_id}"
        event = await self.redis.get(key)
        if event:
            await self.add_to_event_counter(event_id, client_host)
            return EventRead.model_validate_json(event)

        async with self.redis.lock(
            name=f"lock:get_event_{event_id}",
            timeout=5,
            blocking_timeout=3,
        ):
            event = await self.redis.get(key)
            if event:
                await self.add_to_event_counter(event_id, client_host)
                return EventRead.model_validate_json(event)

            event = await self.db.events.get_by_id(event_id)
            if not event:
                raise EventNotFound(event_id)

            await self.add_to_event_counter(event_id, client_host)
            event_read = EventRead.model_validate(event)
            await self.redis.set(
                key,
                event_read.model_dump_json(),
                ex=self._get_event_cache_ttl(),
            )
            return event_read

    async def add_to_event_counter(self, event_id: int, client_host: str | None) -> None:
        if client_host:
            is_unique = await self.redis.set(
                f"event_view:{event_id}:{client_host}",
                "1",
                nx=True,
                ex=EVENT_VIEW_DEDUP_TTL_SECONDS,
            )
            if is_unique:
                await self.event_view_tracker.add_to_queue(event_id)

    def _get_event_cache_ttl(self) -> int:
        return EVENT_CACHE_TTL_SECONDS + random.randint(
            0,
            EVENT_CACHE_TTL_JITTER_SECONDS,
        )
