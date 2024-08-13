import asyncio
import logging
import time
import typing

import orjson
import retry_async

from consumer.domain import models

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
        model: models.Model,
        result_producer: ResultProducer | None = None,
        history_storage: HistoryStorage | None = None,
    ) -> None:
        self._model = model
        self._result_producer = result_producer or DevNullResultProducer()
        self._history_storage = history_storage or InMemoryHistoryStorage()
        # Чтобы нормально работал retry
        self.__name__ = self.__class__.__name__
        self.__qualname__ = self.__class__.__qualname__

    @staticmethod
    def _gather_result(
        model: models.Model,
        history_record: HistoryRecord | None,
        obj: typing.Mapping,
    ) -> tuple[dict[str, int], HistoryRecord]:
        if history_record is None:
            label_history = rD_x = rD_y = None
        else:
            label_history, rD_x, rD_y = history_record

        start = time.time()
        result, new_label_history, new_rD_x, new_rD_y = model.count_complete_ex(
            obj,
            labels_history=label_history,
            old_rD_x=rD_x,
            old_rD_y=rD_y,
        )
        logger.info(f"Result {result} took {time.time() - start} sec")
        return result, [new_label_history, new_rD_x, new_rD_y]

    @retry_async.retry(tries=3, delay=0.05, is_async=True)
    async def __call__(self, key: typing.Optional[bytes], value: typing.Optional[bytes]) -> None:
        value = orjson.loads(value.decode("utf-8"))
        history_key_str = f'{value.get("user_id")}|{value.get("ex_id")}|{value.get("label")}'
        history_record = await self._history_storage.read_history(history_key_str)

        result, new_history_record = await asyncio.to_thread(
            self._gather_result,
            self._model,
            history_record,
            value,
        )

        await self._result_producer.produce(result, value.get("task_id"))
        await self._history_storage.append_to_history(new_history_record, history_key_str)
