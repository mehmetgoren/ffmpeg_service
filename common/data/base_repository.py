from typing import Any
from redis import Redis

from common.data.redis_mapper import RedisMapper


class BaseRepository:
    def __init__(self, connection: Redis, namespace: str):
        self.connection: Redis = connection
        self.namespace: str = namespace
        self._encoding = 'utf-8'

    @staticmethod
    def from_redis(model: Any, redis_binary_dic: dict):
        return RedisMapper(model).from_redis(redis_binary_dic)

    @staticmethod
    def to_redis(model: Any) -> dict:
        return RedisMapper(model).to_redis()
