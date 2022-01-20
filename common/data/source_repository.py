from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository
from common.data.models import Source


class SourceRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'sources:')

    def _get_key(self, identifier: str) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: Source):
        key = self._get_key(model.id)
        dic = model.__dict__
        self.connection.hset(key, mapping=dic)

    def flush_db(self):
        self.connection.flushdb()

    def get(self, identifier: str) -> Source:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        model = Source()
        model.__dict__.update(dic)
        return model

    def get_all(self) -> List[Source]:
        models: List[Source] = []
        keys = self.connection.keys()
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = Source()
            model.__dict__.update(dic)
            models.append(model)
        return models
