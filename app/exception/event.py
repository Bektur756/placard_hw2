from fastapi import HTTPException, status


class EventNotFound(HTTPException):
    def __init__(self, event_id: int | None = None) -> None:
        detail = "Event not found"
        if event_id is not None:
            detail = f"Event with id {event_id} not found"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
