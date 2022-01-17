from redis import Redis
from typing import List

from common.data.base_repository import BaseRepository
from data.models import StreamingModel


class StreamingRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'streaming:')

    def get_connection(self) -> Redis:
        return self.connection

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def add(self, model: StreamingModel) -> int:
        key = self._get_key(model.id)
        dic = model.__dict__
        return self.connection.hset(key, mapping=dic)

    def update(self, model: StreamingModel, field: str) -> int:
        key = self._get_key(model.id)
        dic = model.__dict__
        return self.connection.hset(key, field, dic[field])

    def remove(self, id: str) -> int:
        key = self._get_key(id)
        return self.connection.delete(key)

    def get(self, id: str) -> StreamingModel:
        key = self._get_key(id)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        return StreamingModel().map_from(dic)

    def get_all(self) -> List[StreamingModel]:
        models: List[StreamingModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = StreamingModel().map_from(dic)
            models.append(model)
        return models

    def delete_by_namespace(self) -> int:
        result = 0
        for key in self.connection.scan_iter(self.namespace + '*'):
            result += self.connection.delete(key)
        return result
