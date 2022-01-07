from redis import Redis
from typing import List

from common.utilities import crate_redis_connection, RedisDb
from data.models import StreamingModel


class StreamingRepository:
    def __init__(self):
        self.namespace = 'streaming:'
        self.connection: Redis = crate_redis_connection(RedisDb.SOURCES, True)

    def _get_key(self, model: StreamingModel):
        key = model.id
        return f'{self.namespace}{key}'

    def add(self, model: StreamingModel):
        key = self._get_key(model)
        dic = model.__dict__.copy()
        self.connection.hset(key, mapping=dic)

    def clear(self):
        self.connection.flushdb()

    def get_all(self) -> List[StreamingModel]:
        models: List[StreamingModel] = []
        keys = self.connection.keys()
        for key in keys:
            dic = self.connection.hgetall(key)
            fixed_dic = {k.decode('utf-8'): v.decode('utf-8') for k, v in dic.items()}
            model = StreamingModel().map_from(fixed_dic)
            models.append(model)
        return models
