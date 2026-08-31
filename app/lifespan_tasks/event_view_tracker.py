import asyncio
import time

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
        flush_at: float | None = None
        try:
            while True:
                if not events:
                    events.append(await self.queue.get())
                    flush_at = time.monotonic() + QUEUE_TIMEOUT
                    continue

                if len(events) >= BATCH_SIZE:
                    await self._insert_events_to_db(events)
                    flush_at = None
                    continue

                flush_at = flush_at if flush_at is not None else time.monotonic() + QUEUE_TIMEOUT
                timeout = max(0.0, flush_at - time.monotonic())
                try:
                    event = await asyncio.wait_for(self.queue.get(), timeout)
                except asyncio.TimeoutError:
                    await self._insert_events_to_db(events)
                    flush_at = None
                    continue

                events.append(event)
        finally:
            await self._insert_events_to_db(events)

    async def _insert_events_to_db(self, events: list[int]) -> None:
        if not events:
            return

        event_counts: dict[int, int] = {}
        for event in events:
            event_counts[event] = event_counts.get(event, 0) + 1

        async with database.session() as db:
            await db.events.increment_event_views(event_counts)
            await db.commit()

        events.clear()


event_view_tracker = EventViewTracker()
