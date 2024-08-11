import asyncio
import logging
import random
import time
import typing
from concurrent.futures import process, thread

HistoryRecord: typing.TypeAlias = tuple[list[str] | None, list[float] | None, list[float] | None]

logger = logging.getLogger("points-handler")


class HistoryStorage(typing.Protocol):
    async def read_history(self, key: str) -> HistoryRecord | None:
        pass

    async def append_to_history(self, history_record: HistoryRecord, key: str) -> None:
        pass


class InMemoryHistoryStorage:
    def __init__(self):
        self._history_records: typing.Mapping[str, HistoryRecord] = {}

    async def read_history(self, key: str) -> HistoryRecord | None:
        return self._history_records.get(key)

    async def append_to_history(self, history_record: HistoryRecord, key: str) -> None:
        self._history_records[key] = history_record


class PointsHandler:
    def __init__(
        self,
        history_storage: HistoryStorage = None,
        pool_executor: process.ProcessPoolExecutor | thread.ThreadPoolExecutor | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._history_storage = history_storage or InMemoryHistoryStorage()
        self._executor = pool_executor
        self._loop = loop or asyncio.get_event_loop()
        # Чтобы нормально работал retry
        self.__name__ = self.__class__.__name__
        self.__qualname__ = self.__class__.__qualname__

    @staticmethod
    def _gather_result(history_record: HistoryRecord | None, obj: typing.Mapping) -> HistoryRecord:
        logger.info("handling obj", extra={"obj": obj, "history_record": history_record})
        time.sleep(random.uniform(0.05, 0.01))
        return [], [], []

    async def __call__(self, key: typing.Optional[bytes], value: typing.Optional[bytes]) -> None:
        history_record = await self._history_storage.read_history(key.decode("utf-8"))

        new_record = await self._loop.run_in_executor(
            self._executor,
            self._gather_result,
            history_record,
            value.decode("utf-8"),
        )

        await self._history_storage.append_to_history(new_record, key.decode("utf-8"))
