import asyncio
import functools
import time
import typing
from concurrent.futures import process, thread

HistoryRecord: typing.TypeAlias = tuple[list[str] | None, list[float] | None, list[float] | None]


class HistoryStorage(typing.Protocol):
    async def read_history(self, key: str) -> HistoryRecord | None:
        pass

    async def append_to_history(self, history_record: HistoryRecord, key: str) -> None:
        pass


class PointsHandler:
    def __init__(
        self,
        history_storage: HistoryStorage,
        pool_executor: process.ProcessPoolExecutor | thread.ThreadPoolExecutor | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._history_storage = history_storage
        self._executor = pool_executor
        self._loop = loop or asyncio.get_event_loop()

    def _gather_result(self, history_record: HistoryRecord, obj: typing.Mapping) -> HistoryRecord:
        time.sleep(100)

    async def __call__(self, key: typing.Optional[bytes], value: typing.Optional[bytes]) -> None:
        history_record = await self._history_storage.read_history(key.decode("utf-8"))

        new_record = await self._loop.run_in_executor(
            self._executor,
            functools.partial(self._gather_result, history_record, value.decode("utf-8")),
        )

        await self._history_storage.append_to_history(new_record, key.decode("utf-8"))
