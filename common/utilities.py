import logging
from redis import Redis
from enum import IntEnum
from datetime import datetime

from common.config import Config

logger = logging.getLogger('logger')
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

config: Config = Config.create()


class RedisDb(IntEnum):
    MAIN = 0
    RQ = 1
    EVENTBUS = 15


def crate_redis_connection(db: RedisDb, socket_keepalive: bool = False, health_check_interval: int = 0) -> Redis:
    return Redis(host=config.redis.host, port=config.redis.port, charset='utf-8', db=int(db), socket_keepalive=socket_keepalive,
                 health_check_interval=health_check_interval)


def datetime_now() -> str:
    now = datetime.now()
    sep = '-'
    strings = [''] * 13
    for j in [1, 3, 5, 7, 9, 11]:
        strings[j] = sep
    strings[0] = str(now.year)
    strings[2] = str(now.month)
    strings[4] = str(now.day)
    strings[6] = str(now.hour)
    strings[8] = str(now.minute)
    strings[10] = str(now.second)
    strings[12] = str(now.microsecond)

    return ''.join(strings)
