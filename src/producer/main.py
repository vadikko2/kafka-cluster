import asyncio
import logging
import random
import time
import typing

from producer import producer_application

logging.basicConfig(level="DEBUG")

logger = logging.getLogger("kafka-producer")

logging.getLogger("aiokafka").setLevel("ERROR")
logging.getLogger("asyncio").setLevel("ERROR")

RPS = 1000


def message_factory() -> typing.Iterable[typing.Tuple[bytes, bytes]]:
    counter = 0
    while True:
        for _ in range(RPS):
            yield f"test-key-{counter}".encode("utf-8"), f"test-value-{counter}".encode("utf-8")
            counter += 1
        time.sleep(random.uniform(0, 1))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    producer = producer_application.ProducerApplication(
        bootstrap_servers=["host.docker.internal:29092", "host.docker.internal:29093"],
    )

    logger.info("Starting consumer")
    loop.create_task(producer.produce(topics=["test-kafka"], messages=message_factory()))
    loop.run_forever()
