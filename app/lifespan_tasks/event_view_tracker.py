import asyncio
from app.config.setting import QUEUE_TIMEOUT, BATCH_SIZE
from app.database.db import database


class EventViewTracker:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[int] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._worker_task = asyncio.create_task(self._track_events())

    async def stop(self) -> None:
        if self._worker_task is None:
            return

        self._worker_task.cancel()
        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass

    async def add_to_queue(self, event_id: int) -> None:
        await self.queue.put(event_id)

    async def _track_events(self) -> None:
        events: list[int] = []
        try:
            while True:
                try:
                    event = await asyncio.wait_for(self.queue.get(), timeout=QUEUE_TIMEOUT)
                    events.append(event)
                except asyncio.TimeoutError:
                    if len(events) > 0:
                        await self._insert_events_to_db(events)
                        events = []
                        continue

                if len(events) >= BATCH_SIZE:
                    await self._insert_events_to_db(events)
                    events = []
        finally:
            if events:
                await self._insert_events_to_db(events)

    async def _insert_events_to_db(self, events: list[int]) -> None:
        event_counts: dict[int, int] = {}
        for event in events:
            event_counts[event] = event_counts.get(event, 0) + 1

        async with database.session() as db:
            await db.events.increment_event_views(event_counts)
            await db.commit()


event_view_tracker = EventViewTracker()
