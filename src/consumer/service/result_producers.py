import logging
import typing

import orjson
import redis.asyncio as redis

logger = logging.getLogger("redis-result-producer")


class RedisResultProducer:
    def __init__(self, redis_client: redis.Redis):
        self._redis_client = redis_client

    async def produce(self, value: typing.Dict[str, int], key: str) -> None:
        logger.info(f"Set result key {key}")
        await self._redis_client.publish(key, orjson.dumps(value))
