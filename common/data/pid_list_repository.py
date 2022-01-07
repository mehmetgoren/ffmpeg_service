import os
from redis import Redis
from typing import List

from common.data.base_repository import BaseRepository


class PidListRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'pids:')

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def add(self, service_name: str):
        key = self._get_key(service_name)
        pid = os.getpid()
        self.connection.sadd(key, pid)

    def get(self, service_name: str) -> List[int]:
        return self.connection.smembers(self._get_key(service_name))
