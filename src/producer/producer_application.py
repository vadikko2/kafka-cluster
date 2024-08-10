import asyncio
import functools
import logging
import typing

import aiokafka
import retry_async

logger = logging.getLogger("kafka-producer")

_retry = functools.partial(
    retry_async.retry,
    is_async=True,
)

Key: typing.TypeAlias = typing.Optional[bytes]
Value: typing.TypeAlias = typing.Optional[bytes]
Messages: typing.TypeAlias = typing.Iterable[typing.Tuple[Key, Value]]


class ProducerApplication:
    def __init__(
        self,
        bootstrap_servers: list[str],
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str = "PLAIN",
        sasl_plain_username: str = "",
        sasl_plain_password: str = "",
    ):
        self._bootstrap_servers = bootstrap_servers
        self._security_protocol = security_protocol
        self._sasl_mechanism = sasl_mechanism
        self._sasl_plain_username = sasl_plain_username
        self._sasl_plain_password = sasl_plain_password

    @retry_async.retry(tries=3, delay=15, is_async=True)
    async def produce(
        self,
        topics: list[str],
        messages: Messages,
        loop: asyncio.AbstractEventLoop = None,
    ):
        loop = loop or asyncio.get_event_loop()
        # Создаем продьюсера
        logger.info(
            f"Starting producing to topics {topics} on servers {self._bootstrap_servers}",
        )
        producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            security_protocol=self._security_protocol,
            sasl_mechanism=self._sasl_mechanism,
            sasl_plain_username=self._sasl_plain_username,
            sasl_plain_password=self._sasl_plain_password,
            loop=loop,
        )
        await _retry(tries=3, delay=5)(producer.start)()
        for key, value in messages:
            for topic in topics:
                logger.info(f"Producing message {key}:{value} to topic {topic}")
                await _retry(tries=3, delay=5)(producer.send_and_wait)(topic, value=value, key=key)

        await _retry(tries=3, delay=5)(producer.stop)()
