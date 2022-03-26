from redis import Redis
from typing import List

from common.data.base_repository import BaseRepository
from stream.stream_model import StreamModel


class StreamRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'streams:')

    def get_connection(self) -> Redis:
        return self.connection

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def add(self, model: StreamModel) -> int:
        key = self._get_key(model.id)
        dic = self.to_redis(model)
        return self.connection.hset(key, mapping=dic)

    def remove(self, identifier: str) -> int:
        key = self._get_key(identifier)
        return self.connection.delete(key)

    def get(self, identifier: str) -> StreamModel:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        model: StreamModel = self.from_redis(StreamModel(), dic)
        model.set_paths()
        return model

    def get_all(self) -> List[StreamModel]:
        models: List[StreamModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            model: StreamModel = self.from_redis(StreamModel(), dic)
            model.set_paths()
            models.append(model)
        return models

    def delete_by_namespace(self) -> int:
        result = 0
        for key in self.connection.scan_iter(self.namespace + '*'):
            result += self.connection.delete(key)
        return result
