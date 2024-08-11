import asyncio
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from aioprometheus import Gauge, Histogram, Summary, timer

from consumer.adapters import settings

# Service statuses consts
STATUS_HEALTHY = 2
STATUS_DEGRADATION = 1
STATUS_UNAVAILABLE = 0

healthcheck = Gauge(settings.config["Service"]["service_name"] + "_healthcheck", "Gauge")
healthcheck_histogram = Histogram(
    settings.config["Service"]["service_name"] + "_healthcheck_duration_seconds",
    "Histogram",
)
healthcheck_summary = Summary(
    settings.config["Service"]["service_name"] + "_healthcheck_duration_seconds" + "_summary",
    "Summary",
)

latency_histogram = Histogram(settings.config["Service"]["service_name"] + "_latency_duration_seconds", "Histogram")
latency_summary = Summary(
    settings.config["Service"]["service_name"] + "_latency_duration_seconds" + "_summary",
    "Summary",
)

timer = timer


def hist_timer(metric: Histogram, labels: dict[str, str] = None) -> Callable[..., Any]:
    """
    This decorator wraps a callable with code to calculate how long the
    callable takes to execute and updates the metric with the duration.

    :param metric: a metric to update with the calculated function duration.
      The metric object must be a Histogram metric object.

    :param labels: a dict of extra labels to associate with the metric.

    :return: a callable wrapping the decorated function. The callable will
      be awaitable if the wrapped function was a coroutine function.
    """
    if not isinstance(metric, Histogram):
        raise Exception(f"timer decorator expects a Histogram metric but got: {metric}")

    def measure(func):
        """
        This function wraps the callable with timing and metric updating logic.

        :param func: the callable to be timed.

        :returns: the return value from the decorated callable.
        """

        @wraps(func)
        async def async_func_wrapper(*args, **kwds):
            start_time = time.monotonic()
            rv = func(*args, **kwds)
            if isinstance(rv, asyncio.Future) or asyncio.iscoroutine(rv):
                try:
                    rv = await rv
                finally:
                    metric.add(labels, time.monotonic() - start_time)
            return rv

        @wraps(func)
        def func_wrapper(*args, **kwds):
            start_time = time.monotonic()
            try:
                rv = func(*args, **kwds)
            finally:
                metric.add(labels, time.monotonic() - start_time)
            return rv

        if asyncio.iscoroutinefunction(func):
            return async_func_wrapper
        return func_wrapper

    return measure
