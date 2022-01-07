from redis import Redis
from typing import List

from common.data.base_repository import BaseRepository
from data.models import StreamingModel


class StreamingRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'streaming:')

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def add(self, model: StreamingModel):
        key = self._get_key(model.name)
        dic = model.__dict__.copy()
        self.connection.hset(key, mapping=dic)

    def get(self, name: str) -> StreamingModel:
        key = self._get_key(name)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        return StreamingModel().map_from(dic)

    def get_all(self) -> List[StreamingModel]:
        models: List[StreamingModel] = []
        keys = self.connection.keys()
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = StreamingModel().map_from(dic)
            models.append(model)
        return models

    def clear(self):
        self.connection.flushdb()
