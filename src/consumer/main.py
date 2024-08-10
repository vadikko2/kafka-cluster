import asyncio
import logging

import aiokafka

from consumer import consumer_application

logging.basicConfig(level="DEBUG")

logger = logging.getLogger("kafka-consumer")

logging.getLogger("aiokafka").setLevel("ERROR")
logging.getLogger("asyncio").setLevel("ERROR")

CONSUMERS_NUMBER = 2


async def on_message(record: aiokafka.ConsumerRecord) -> None:
    logger.info(f"Handled message from {record.topic}: {record.value}")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    consumer = consumer_application.ConsumerApplication(
        bootstrap_servers=["host.docker.internal:29092", "host.docker.internal:29093"],
        group_id="test-consumer",
    )

    logger.info("Starting consumer")
    for consumer_number in range(CONSUMERS_NUMBER):
        loop.create_task(
            consumer.start(
                consumer_name=f"consumer-{consumer_number + 1}",
                topics=["test-kafka"],
                handler=on_message,
            ),
        )

    loop.run_forever()
