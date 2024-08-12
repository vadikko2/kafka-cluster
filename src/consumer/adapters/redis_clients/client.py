import time

import orjson
from loguru import logger
from redis.asyncio import Redis

from consumer.adapters import metrics, settings


class CustomRedis(Redis):
    def __init__(self, service_type="Redis"):
        super().__init__(
            host=settings.config[service_type]["host"],
            port=settings.config[service_type]["port"],
            username=settings.config[service_type]["username"],
            password=settings.config[service_type]["password"],
        )

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

        return orjson.loads(result)

    @metrics.hist_timer(metrics.healthcheck_histogram, {"healthcheck": "redis"})
    @metrics.timer(metrics.healthcheck_summary, {"healthcheck": "redis"})
    async def readiness(self):
        try:
            st_t = time.time()  # noqa F841
            res = await self.keys("*")  # noqa F841
            end_t = time.time()  # noqa F841
            if res:
                wait_time = end_t - st_t
            if wait_time < 2:
                metrics.healthcheck.set({"healthcheck": "redis"}, metrics.STATUS_HEALTHY)
            else:
                metrics.healthcheck.set({"healthcheck": "redis"}, metrics.STATUS_DEGRADATION)
            return True
        except Exception as err:
            logger.exception(err)
            # metrics.healthcheck.set({"healthcheck": "redis"}, metrics.STATUS_UNAVAILABLE)

        return False
