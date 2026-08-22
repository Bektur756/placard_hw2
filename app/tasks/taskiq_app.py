from taskiq import SimpleRetryMiddleware, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisStreamBroker
from app.config.setting import REDIS_URL


broker_async = RedisStreamBroker(
    url=REDIS_URL,
    queue_name="taskiq_queue",
    socket_timeout=None,
    xread_count=1,
).with_middlewares(SimpleRetryMiddleware(
    types_of_exceptions=(Exception,)
))

broker_cpu = RedisStreamBroker(
    url=REDIS_URL,
    queue_name="taskiq_queue_two",
    socket_timeout=None,
    xread_count=1,
).with_middlewares(SimpleRetryMiddleware(
    types_of_exceptions=(Exception,)
))

scheduler = TaskiqScheduler(
    broker=broker_async,
    sources=[LabelScheduleSource(broker=broker_async)]
)
