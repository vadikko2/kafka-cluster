import asyncio
import logging
from concurrent.futures import process

from consumer.adapters import consumer_application, settings
from consumer.adapters.redis_clients import client
from consumer.service import history_storages, points_handler, result_producers

logging.basicConfig(level="DEBUG")

logger = logging.getLogger("kafka-consumer")

logging.getLogger("aiokafka").setLevel("ERROR")
logging.getLogger("asyncio").setLevel("ERROR")

CONSUMERS_NUMBER = 1
POOL_SIZE = 2


async def on_message(key: consumer_application.Key, value: consumer_application.Value) -> None:
    logger.info(f"Handled message key={key}, value={value}")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    consumer = consumer_application.ConsumerApplication(
        # bootstrap_servers=["host.docker.internal:29092", "host.docker.internal:29093"],
        bootstrap_servers=settings.config["KafkaConsumer"]["servers"],
        group_id=settings.config["KafkaConsumer"]["consumer_group_id"],
    )

    logger.info("Starting consumer")
    with process.ProcessPoolExecutor(max_workers=POOL_SIZE) as pool:
        for consumer_number in range(CONSUMERS_NUMBER):
            redis_client = client.CustomRedis()
            loop.create_task(
                consumer.start(
                    consumer_name=f"consumer-{consumer_number + 1}",
                    topics=[settings.config["KafkaConsumer"]["topic"]],
                    handler=points_handler.PointsHandler(
                        pool_executor=pool,
                        result_producer=result_producers.RedisResultProducer(redis_client=redis_client),
                        history_storage=history_storages.RedisHistoryStorage(redis_client=redis_client),
                    ),
                    loop=loop,
                    consumer_batch_size=1000,
                    consumer_timeout_ms=1,
                ),
            )

        loop.run_forever()
