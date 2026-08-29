class EventNotFound(Exception):
    def __init__(self, event_id: int | None = None) -> None:
        detail = "Event not found"
        if event_id is not None:
            detail = f"Event with id {event_id} not found"

        self.detail = detail
        super().__init__(detail)
