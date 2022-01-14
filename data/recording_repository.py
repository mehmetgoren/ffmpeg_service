from redis import Redis
from typing import List

from common.data.base_repository import BaseRepository
from data.models import RecordingModel


class RecordingRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'recording:')

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def get_connection(self) -> Redis:
        return self.connection

    def add(self, model: RecordingModel) -> int:
        key = self._get_key(model.id)
        dic = model.__dict__
        return self.connection.hset(key, mapping=dic)

    def update(self, model: RecordingModel, field: str) -> int:
        key = self._get_key(model.id)
        dic = model.__dict__
        return self.connection.hset(key, field, dic[field])

    def get(self, id: str) -> RecordingModel:
        key = self._get_key(id)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        return RecordingModel().map_from(dic)

    def get_all(self) -> List[RecordingModel]:
        models: List[RecordingModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = RecordingModel().map_from(dic)
            models.append(model)
        return models
