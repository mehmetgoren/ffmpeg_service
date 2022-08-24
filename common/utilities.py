import logging
from redis import Redis
from enum import IntEnum
from datetime import datetime

from common.config import Config, config_redis

logger = logging.getLogger('logger')
logger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.WARNING)

config: Config = Config.create()


class RedisDb(IntEnum):
    MAIN = 0
    RQ = 1
    RQ2 = 2
    EVENTBUS = 15


def crate_redis_connection(db: RedisDb, socket_keepalive: bool = False, health_check_interval: int = 0) -> Redis:
    return Redis(host=config_redis.host, port=config_redis.port, charset='utf-8', db=int(db), socket_keepalive=socket_keepalive,
                 health_check_interval=health_check_interval)


def fix_zero_s(val_str: str) -> str:
    if len(val_str) == 1:
        return f'0{val_str}'
    return val_str


def fix_zero(val: int) -> str:
    return str(val) if val > 9 else f'0{val}'


def datetime_now() -> str:
    now = datetime.now()
    sep = '_'
    strings = [''] * 13
    for j in [1, 3, 5, 7, 9, 11]:
        strings[j] = sep
    strings[0] = str(now.year)
    strings[2] = fix_zero(now.month)
    strings[4] = fix_zero(now.day)
    strings[6] = fix_zero(now.hour)
    strings[8] = fix_zero(now.minute)
    strings[10] = fix_zero(now.second)
    strings[12] = fix_zero(now.microsecond)

    return ''.join(strings)
