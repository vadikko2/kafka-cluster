import logging
import typing

import orjson
import redis.asyncio as redis
import retry_async

logger = logging.getLogger("redis-result-producer")


class RedisResultProducer:
    def __init__(self, redis_client: redis.Redis):
        self._redis_client = redis_client

    @retry_async.retry(tries=3, delay=0.05, is_async=True)
    async def produce(self, value: typing.Dict[str, int], key: str) -> None:
        logger.info(f"Produce result {value} key {key}")
        await self._redis_client.publish(key, orjson.dumps(value))
