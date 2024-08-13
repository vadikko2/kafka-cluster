import json
import time

from loguru import logger
from redis import RedisError
from redis.asyncio import sentinel

from consumer.adapters import metrics, settings

ERROR_KEY_NOT_FOUND = "Key not found in redis"


class RedisDriver:
    def __init__(self, service_type="Sentinel"):
        self.service_type = service_type
        self.redis_config = {
            "service_name": settings.config[service_type]["redis_master_name"],
            "sentinel_host": settings.config[service_type]["host"],
            "sentinel_port": settings.config[service_type]["port"],
        }
        self.service = self.redis_config["service_name"]
        self.__connect(self.redis_config)

    def __connect(self, redis_config):
        self.connection = sentinel.Sentinel(
            [
                (redis_config["sentinel_host"], redis_config["sentinel_port"]),
            ],
            socket_timeout=float(settings.config[self.service_type]["socket_timeout"]),
            password=settings.config[self.service_type]["password"],
        )

    async def set(self, key, value, ex):
        try:
            master = self.connection.master_for(self.service)
            await master.set(key, value, ex)
            await master.close()
            return True
        except RedisError as err:
            logger.exception(f"Error while connecting to redis : {str(err)}")
            return False

    async def get(self, key):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            value = await master.get(key_str)
            await master.close()
        except RedisError as err:
            logger.exception(f"Error while retrieving value from redis : {str(err)}")
            return False

        if value is not None:
            return value
        else:
            return False

    async def delete(self, key):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            value = await master.delete(key_str)  # noqa F841
            await master.close()
        except RedisError as err:
            logger.exception(f"EError while deleting key from redis : {str(err)}")
            return False

        return True

    def pubsub(self):
        try:
            master = self.connection.master_for(self.service)
            ps = master.pubsub()
        except RedisError as err:
            logger.exception(f"Error while create pubsub (redis): {str(err)}")
            return False

        if ps is not None:
            return ps
        else:
            return False

    @metrics.hist_timer(metrics.latency_histogram, {"latency": "redis"})
    @metrics.timer(metrics.latency_summary, {"latency": "redis"})
    async def redis_result(self, ps):

        count = False
        async for message in ps.listen():
            if not count:
                count = True
                continue

            result = message["data"]
            break

        await ps.unsubscribe()
        await ps.close()

        return json.loads(result)

    async def publish(self, key, value, ex):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            await master.publish(key_str, value, ex=ex)
            await master.close()
        except RedisError as err:
            logger.exception(f"Error while publish value to redis sub: {str(err)}")

    @metrics.hist_timer(metrics.healthcheck_histogram, {"healthcheck": "redis"})
    @metrics.timer(metrics.healthcheck_summary, {"healthcheck": "redis"})
    async def readiness(self):
        try:
            st_t = time.time()
            master = self.connection.master_for(self.service)
            await master.set(f'{settings.config["Service"]["service_name"]}|readiness', "readiness", 2)
            await master.close()
            end_t = time.time()
            wait_time = end_t - st_t
            if wait_time < 2:
                metrics.healthcheck.set({"healthcheck": "redis"}, metrics.STATUS_HEALTHY)
            else:
                metrics.healthcheck.set({"healthcheck": "redis"}, metrics.STATUS_DEGRADATION)
            return True
        except Exception as err:
            logger.exception(err)
            metrics.healthcheck.set({"healthcheck": "redis"}, metrics.STATUS_UNAVAILABLE)

        return False
