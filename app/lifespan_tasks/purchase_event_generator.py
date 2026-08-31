import asyncio
import json
import logging
import random
from datetime import UTC, datetime
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from app.config.setting import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_PRODUCER_LINGER_MS,
    PURCHASE_EVENT_GENERATOR_INTERVAL_SECONDS,
    PURCHASE_EVENT_GENERATOR_MAX_BATCH_SIZE,
    PURCHASE_EVENT_GENERATOR_MIN_BATCH_SIZE,
    PURCHASE_EVENTS_TOPIC,
)


logger = logging.getLogger(__name__)


class PurchaseEventGenerator:
    def __init__(self) -> None:
        self.task: asyncio.Task[None] | None = None
        self.producer: AIOKafkaProducer | None = None

    def start(self) -> None:
        self.task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def run(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            linger_ms=KAFKA_PRODUCER_LINGER_MS,
            value_serializer=lambda value: json.dumps(value).encode(),
            key_serializer=lambda value: str(value).encode(),
        )

        try:
            await self.producer.start()
            while True:
                await self.send_batch()
                await asyncio.sleep(PURCHASE_EVENT_GENERATOR_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Purchase event generator failed")
        finally:
            await self.producer.stop()
            self.producer = None

    async def send_batch(self) -> None:
        if self.producer is None:
            return

        batch_size = random.randint(
            PURCHASE_EVENT_GENERATOR_MIN_BATCH_SIZE,
            PURCHASE_EVENT_GENERATOR_MAX_BATCH_SIZE,
        )
        futures = []
        for _ in range(batch_size):
            event = self.build_event()
            future = await self.producer.send(
                PURCHASE_EVENTS_TOPIC,
                value=event,
                key=event["event_id"],
            )
            futures.append(future)

        await asyncio.gather(*futures)

    def build_event(self) -> dict[str, int | str]:
        event_id = random.randint(1, 5)
        tickets_count = random.randint(1, 5)
        ticket_price = random.choice((1500, 2000, 2500, 3000, 4000))
        total_amount = tickets_count * ticket_price

        return {
            "event_type": "tickets.purchased",
            "payment_id": uuid4().hex[:8],
            "event_id": event_id,
            "tickets_count": tickets_count,
            "total_amount": total_amount,
            "paid_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }


purchase_event_generator = PurchaseEventGenerator()
