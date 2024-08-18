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


def bootstrap_on_message(model_path: str | None = None) -> consumer_application.Handler:
    """Ининциализация обработчика событий"""
    model_path = model_path or settings.config["Model"]["model_path"]
    with open(model_path + ".dat", "rb") as f:
        model = pkl.load(f)

    with open(model_path + ".meta", "rt") as f:
        meta = json.load(f)

    return points_handler.PointsHandler(
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
        result_producer=result_producers.RedisResultProducer(
            redis_client=client.CustomRedis(),
        ),
        history_storage=history_storages.RedisHistoryStorage(
            redis_client=client.CustomRedis(),
            ttl=int(settings.config["Redis"]["ttl"]),
        ),
    )


def bootstrap_consumer_task(
    on_message: consumer_application.Handler,
    loop: asyncio.AbstractEventLoop,
) -> typing.Coroutine:
    """Ининциализация консьюмера"""
    return consumer_application.ConsumerApplication(
        bootstrap_servers=settings.config["KafkaConsumer"]["servers"],
        group_id=settings.config["KafkaConsumer"]["consumer_group_id"],
    ).start(
        consumer_name=f"consumer-{consumer_number + 1}",
        topics=[settings.config["KafkaConsumer"]["topic"]],
        handler=on_message,
        loop=loop,
        consumer_batch_size=int(
            settings.config["KafkaConsumer"]["consumer_batch_size"],
        ),
        consumer_timeout_ms=int(
            settings.config["KafkaConsumer"]["consumer_timeout_ms"],
        ),
    )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = []

    logger.info("Starting consumer")
    for consumer_number in range(CONSUMERS_NUMBER):
        tasks.append(bootstrap_consumer_task(bootstrap_on_message(), loop=loop))
    loop.run_until_complete(asyncio.gather(*tasks))
