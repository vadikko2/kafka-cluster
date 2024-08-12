import asyncio
import json
import logging
import pickle as pkl
import typing

from consumer.adapters import consumer_application, settings
from consumer.adapters.redis_clients import client
from consumer.domain import models, pose_classifiers, pose_descriptors
from consumer.service import history_storages, points_handler, result_producers

logging.basicConfig(level="DEBUG")

logger = logging.getLogger("kafka-consumer")

logging.getLogger("aiokafka").setLevel("ERROR")
logging.getLogger("asyncio").setLevel("ERROR")

CONSUMERS_NUMBER = int(settings.config["Service"]["consumers_number"])
POOL_SIZE = int(settings.config["Service"]["pool_size"])


async def on_message(key: consumer_application.Key, value: consumer_application.Value) -> None:
    logger.info(f"Handled message key={key}, value={value}")


def load_artifacts(model_path: str) -> typing.Tuple[pose_classifiers.ModelType, typing.Dict]:
    with open(model_path + ".dat", "rb") as f:
        model = pkl.load(f)

    with open(model_path + ".meta", "rt") as f:
        meta = json.load(f)

    return model, meta


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = []

    logger.info("Starting consumer")

    executor = None

    if settings.config["Service"]["executor"].lower() == "thread":
        from concurrent.futures import thread

        executor = thread.ThreadPoolExecutor
    elif settings.config["Service"]["executor"].lower() == "process":
        from concurrent.futures import process

        executor = process.ProcessPoolExecutor

    with executor(max_workers=POOL_SIZE) as pool:
        for consumer_number in range(CONSUMERS_NUMBER):
            model, meta = load_artifacts(
                settings.config["Model"]["model_path"],
            )
            tasks.append(
                consumer_application.ConsumerApplication(
                    # bootstrap_servers=["host.docker.internal:29092", "host.docker.internal:29093"],
                    bootstrap_servers=settings.config["KafkaConsumer"]["servers"],
                    group_id=settings.config["KafkaConsumer"]["consumer_group_id"],
                ).start(
                    consumer_name=f"consumer-{consumer_number + 1}",
                    topics=[settings.config["KafkaConsumer"]["topic"]],
                    handler=points_handler.PointsHandler(
                        model=models.Model(
                            pose_clf=pose_classifiers.PoseClassifier(
                                model=model,
                                descriptor=pose_descriptors.PoseDescriptor(
                                    image_w=settings.config["Model"]["write_width"],
                                    image_h=settings.config["Model"]["write_height"],
                                    threshold=settings.config["Model"]["bip_threshold"],
                                ),
                                meta=meta,
                            ),
                            model_config=settings.config["Model"],
                        ),
                        pool_executor=pool,
                        result_producer=result_producers.RedisResultProducer(redis_client=client.CustomRedis()),
                        history_storage=history_storages.RedisHistoryStorage(
                            redis_client=client.CustomRedis(),
                            ttl=int(settings.config["Redis"]["ttl"]),
                        ),
                    ),
                    loop=loop,
                    consumer_batch_size=int(settings.config["KafkaConsumer"]["consumer_batch_size"]),
                    consumer_timeout_ms=int(settings.config["KafkaConsumer"]["consumer_timeout_ms"]),
                ),
            )

        loop.run_until_complete(asyncio.gather(*tasks))
        # loop.run_forever()
