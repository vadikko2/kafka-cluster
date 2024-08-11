import typing

import redis.asyncio as redis

HistoryRecord: typing.TypeAlias = tuple[list[str] | None, list[float] | None, list[float] | None]


class RedisHistoryStorage:
    def __init__(self, redis_client: redis.Redis):
        self._redis_client = redis_client

    async def read_history(self, key: str) -> HistoryRecord | None:
        ...

    async def append_to_history(self, history_record: HistoryRecord, key: str) -> None:
        ...
