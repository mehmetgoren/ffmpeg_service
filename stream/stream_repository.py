from redis import Redis
from typing import List

from common.data.base_repository import BaseRepository, fix_dic_fields_bool_to_int
from stream.stream_model import StreamModel


class StreamRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'stream:')

    def get_connection(self) -> Redis:
        return self.connection

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def add(self, model: StreamModel) -> int:
        key = self._get_key(model.id)
        dic = model.__dict__
        fix_dic_fields_bool_to_int(dic)
        return self.connection.hset(key, mapping=dic)

    def update(self, model: StreamModel, fields: List[str]) -> int:
        key = self._get_key(model.id)
        dic = {}
        for field in fields:
            dic[field] = model.__dict__[field]
        return self.connection.hset(key, mapping=dic)

    def remove(self, identifier: str) -> int:
        key = self._get_key(identifier)
        return self.connection.delete(key)

    def get(self, identifier: str) -> StreamModel:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        return StreamModel().map_from(dic)

    def get_all(self) -> List[StreamModel]:
        models: List[StreamModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = StreamModel().map_from(dic)

            models.append(model)
        return models

    def delete_by_namespace(self) -> int:
        result = 0
        for key in self.connection.scan_iter(self.namespace + '*'):
            result += self.connection.delete(key)
        return result
