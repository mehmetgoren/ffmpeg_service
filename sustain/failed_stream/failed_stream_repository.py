from __future__ import annotations

from redis.client import Redis

from common.data.base_repository import BaseRepository
from sustain.failed_stream.failed_stream_model import FailedStreamModel


class FailedStreamRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'failed_streams:')

    def _get_key(self, identifier: str) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: FailedStreamModel):
        key = self._get_key(model.id)
        dic = self.to_redis(model)
        self.connection.hset(key, mapping=dic)

    def remove_all(self) -> int:
        r = self.connection
        count = 0
        for key in r.scan_iter(f'{self.namespace}*'):
            count += r.delete(key)
        return count

    def get(self, identifier: str) -> FailedStreamModel | None:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        return self.from_redis(FailedStreamModel(), dic)
