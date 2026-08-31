from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.lifespan_tasks.add_event_data import add_event_data_to_db
from app.lifespan_tasks.event_view_tracker import event_view_tracker
from app.lifespan_tasks.purchase_event_generator import purchase_event_generator
from app.config.httpx_client import close_httpx_clients
from app.config.redis_client import redis_service
from app.exception.checkout import (
    DuplicateSeatIdsError,
    PaymentUnavailableError,
    SeatsNotAvailableError,
)
from app.exception.event import EventNotFound
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await add_event_data_to_db()
    event_view_tracker.start()
    purchase_event_generator.start()
    yield
    await purchase_event_generator.stop()
    await event_view_tracker.stop()
    await redis_service.close()
    await close_httpx_clients()


app = FastAPI(title="API Афиши", lifespan=lifespan)


@app.exception_handler(DuplicateSeatIdsError)
async def duplicate_seat_ids_handler(_, exc: DuplicateSeatIdsError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(EventNotFound)
async def event_not_found_handler(_, exc: EventNotFound) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


@app.exception_handler(SeatsNotAvailableError)
async def seats_not_available_handler(_, exc: SeatsNotAvailableError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )


@app.exception_handler(PaymentUnavailableError)
async def payment_unavailable_handler(_, exc: PaymentUnavailableError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": exc.detail},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
