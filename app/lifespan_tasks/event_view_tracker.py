import asyncio
from app.database.db import database


BATCH_SIZE = 10
QUEUE_TIMEOUT = 5


class EventViewTracker:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[int | None] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._track_events())

    async def stop(self) -> None:
        if self._worker_task is None:
            return

        await self.queue.put(None)
        await self._worker_task

    async def add_to_queue(self, event_id: int) -> None:
        await self.queue.put(event_id)

    async def _track_events(self) -> None:
        events: list[int] = []
        while True:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=QUEUE_TIMEOUT)
                if event is None:
                    self.queue.task_done()
                    break

                events.append(event)
            except asyncio.TimeoutError:
                if events:
                    await self._insert_events_to_db(events)
                    events = []
                continue

            if len(events) >= BATCH_SIZE:
                await self._insert_events_to_db(events)
                events = []

            self.queue.task_done()

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
