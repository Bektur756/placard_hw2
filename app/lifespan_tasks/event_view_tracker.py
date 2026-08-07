import asyncio


class EventViewTracker:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def start(self):
        self._worker_stask = asyncio.create_task(self._track_events())

    async def stop(self):
        self._worker_stask.cancel()

        try:
            await self._worker_stask
        except:
            pass

    async def add_to_queue(self, event_id):
        await self.queue.put(event_id)

    async def _track_events(self):
        events = []
        while True:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=5)
                events.append(event)
            except asyncio.TimeoutError:
                if events:
                    await self._insert_events_to_db(events)
                    events = []

            if len(events) > 10:
                await self._insert_events_to_db(events)
                events = []

    async def _insert_events_to_db(self, events):
        pass


event_view_tracker = EventViewTracker()
