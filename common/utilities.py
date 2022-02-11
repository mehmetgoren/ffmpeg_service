import logging
from redis import Redis
from enum import IntEnum
from datetime import datetime

from common.config import Config

logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

config: Config = Config.create()


class RedisDb(IntEnum):
    MAIN = 0
    RQ = 1
    EVENTBUS = 15


def crate_redis_connection(db: RedisDb) -> Redis:
    return Redis(host=config.redis.host, port=config.redis.port, charset='utf-8', db=int(db))


def datetime_now():
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
