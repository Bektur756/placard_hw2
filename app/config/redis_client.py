from app.config.setting import REDIS_URL
from redis.asyncio import Redis


class RedisService:
    def __init__(self) -> None:
        self.redis = Redis.from_url(REDIS_URL, decode_responses=True)

    async def close(self) -> None:
        await self.redis.aclose()

redis_service = RedisService()
