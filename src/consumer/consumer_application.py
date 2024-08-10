import asyncio
import functools
import logging
import typing

import aiokafka
import retry_async

logger = logging.getLogger("kafka-consumer")

Handler: typing.TypeAlias = typing.Callable[[aiokafka.ConsumerRecord], typing.Awaitable[None]]

_retry = functools.partial(
    retry_async.retry,
    is_async=True,
)


class ConsumerApplication:
    def __init__(self, bootstrap_servers: list[str], group_id: str):
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id

    @staticmethod
    async def _consume(
        consumer: aiokafka.AIOKafkaConsumer,
        handler: Handler,
        consumer_timeout_ms: int,
        consumer_batch_size: int,
    ):
        while True:
            # Читаем пачку сообщений. Делаем это именно таким образом, потому что не хотим, чтобы происходил autocommit
            records = await consumer.getmany(timeout_ms=consumer_timeout_ms, max_records=consumer_batch_size)
            for tp, messages in records.items():
                if not messages:
                    logger.info("No messages received, sleep")
                    await asyncio.sleep(consumer_timeout_ms / 1000)
                    continue

                for msg in messages:
                    logger.info(
                        f"Received message from {msg.topic}: {msg.value}",
                        extra={"topic": msg.topic},
                    )
                    # До победного пытаемся обработать сообщение
                    await _retry(tries=3, delay=5)(handler)(msg)
                    # Делаем commit только по тем сообщениям, которые обработали
                    await _retry(tries=3, delay=5)(consumer.commit)({tp: msg.offset + 1})
                    logger.info(f"Offset {msg.offset + 1} for topic {msg.topic} committed")

    async def start(
        self,
        topics: list[str],
        handler: Handler,
        consumer_batch_size: int = 100,
        consumer_timeout_ms: int = 500,
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str = "PLAIN",
        sasl_plain_username: str = "",
        sasl_plain_password: str = "",
        loop: asyncio.AbstractEventLoop = None,
    ):
        """Данный метод является единицей, которую можно запускать в отдельном потоке."""
        loop = loop or asyncio.get_event_loop()
        # Создаем консьюмера в группе
        consumer = aiokafka.AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            fetch_max_wait_ms=consumer_timeout_ms,
            enable_auto_commit=False,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=sasl_plain_username,
            sasl_plain_password=sasl_plain_password,
            loop=loop,
        )

        await _retry(tries=3, delay=5)(consumer.start)()
        try:
            await self._consume(consumer, handler, consumer_timeout_ms, consumer_batch_size)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
        finally:
            await _retry(tries=3, delay=5)(consumer.stop)()
