import orjson
import redis.asyncio as redis

from consumer.service import points_handler


class RedisResultProducer:
    def __init__(self, redis_client: redis.Redis):
        self._redis_client = redis_client

    async def produce(self, value: points_handler.Result, key: str) -> None:
        await self._redis_client.publish(key, orjson.dumps(value.model_dump(mode="json")))
