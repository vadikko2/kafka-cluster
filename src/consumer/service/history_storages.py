import orjson
import redis.asyncio as redis

from consumer.service import points_handler


class RedisHistoryStorage:
    def __init__(self, redis_client: redis.Redis):
        self._redis_client = redis_client

    async def read_history(self, key: str) -> points_handler.HistoryRecord | None:
        record = await self._redis_client.get(key)
        return record and orjson.loads(record)

    async def append_to_history(self, history_record: points_handler.HistoryRecord, key: str) -> None:
        await self._redis_client.set(key, orjson.dumps(history_record))
