from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository
from sustain.rec_stuck.rec_stuck_model import RecStuckModel


class RecStuckRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'recstucks:')

    def _get_key(self, identifier: str) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: RecStuckModel):
        key = self._get_key(model.id)
        dic = self.to_redis(model)
        self.connection.hset(key, mapping=dic)

    def remove_all(self) -> int:
        r = self.connection
        count = 0
        for key in r.scan_iter(f'{self.namespace}*'):
            count += r.delete(key)
        return count

    def remove(self, model: RecStuckModel) -> int:
        key = self._get_key(model.id)
        return self.connection.delete(key)

    def get_all(self) -> List[RecStuckModel]:
        models: List[RecStuckModel] = []
        keys = self.connection.keys(f'{self.namespace}*')
        for key in keys:
            dic = self.connection.hgetall(key)
            model: RecStuckModel = self.from_redis(RecStuckModel(), dic)
            models.append(model)
        return models

    def get(self, identifier: str) -> RecStuckModel:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        return self.from_redis(RecStuckModel(), dic)
