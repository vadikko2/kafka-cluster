import asyncio
import logging
import random
import time
import typing
from concurrent.futures import process, thread

HistoryRecord: typing.TypeAlias = list[list[str] | list[float]]

logger = logging.getLogger("points-handler")


class ResultProducer(typing.Protocol):
    async def produce(self, value: typing.Dict[str, int], key: str) -> None:
        pass


class DevNullResultProducer:
    async def produce(self, value: typing.Dict[str, int], key: str) -> None:
        logger.warning(f"Resul {value} for key {key} will we lost")


class HistoryStorage(typing.Protocol):
    async def read_history(self, key: str) -> HistoryRecord | None:
        pass

    async def append_to_history(self, history_record: HistoryRecord, key: str) -> None:
        pass


class InMemoryHistoryStorage:
    def __init__(self):
        self._history_records: typing.Dict[str, HistoryRecord] = {}

    async def read_history(self, key: str) -> HistoryRecord | None:
        return self._history_records.get(key)

    async def append_to_history(self, history_record: HistoryRecord, key: str) -> None:
        self._history_records[key] = history_record


class PointsHandler:
    def __init__(
        self,
        result_producer: ResultProducer | None = None,
        history_storage: HistoryStorage | None = None,
        pool_executor: process.ProcessPoolExecutor | thread.ThreadPoolExecutor | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._result_producer = result_producer or DevNullResultProducer()
        self._history_storage = history_storage or InMemoryHistoryStorage()
        self._executor = pool_executor
        self._loop = loop or asyncio.get_event_loop()
        # Чтобы нормально работал retry
        self.__name__ = self.__class__.__name__
        self.__qualname__ = self.__class__.__qualname__

    @staticmethod
    def _gather_result(history_record: HistoryRecord | None, obj: typing.Mapping) -> HistoryRecord:
        start = time.time()
        time.sleep(random.uniform(0.005, 0.01))
        logger.info(f"Handling ETA {time.time() - start} seconds")
        return [[], [], []]  # noqa

    async def __call__(self, key: typing.Optional[bytes], value: typing.Optional[bytes]) -> None:
        history_record = await self._history_storage.read_history(key.decode("utf-8"))
        key_str = key.decode("utf-8")

        new_record = await self._loop.run_in_executor(
            self._executor,
            self._gather_result,
            history_record,
            value.decode("utf-8"),
        )

        await self._result_producer.produce(
            {
                "squats": 3,
            },
            key_str,
        )

        await self._history_storage.append_to_history(new_record, key_str)
