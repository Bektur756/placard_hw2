from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.lifespan_tasks.add_event_data import add_event_data_to_db
from app.lifespan_tasks.event_view_tracker import event_view_tracker
from app.config.httpx_client import close_httpx_clients
from app.config.redis_client import redis_service
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await add_event_data_to_db()
    event_view_tracker.start()
    yield
    await event_view_tracker.stop()
    await redis_service.close()
    await close_httpx_clients()


app = FastAPI(title="API Афиши", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
