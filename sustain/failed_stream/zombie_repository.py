from redis.client import Redis

from common.data.base_repository import BaseRepository


class ZombieRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'zombies:')

    def _get_key(self, key: str):
        return f'{self.namespace}{key}'

    def add(self, key: str, value: str):
        key = self._get_key(key)
        self.connection.sadd(key, value)

    def remove_all(self) -> int:
        r = self.connection
        count = 0
        for key in r.scan_iter(f'{self.namespace}*'):
            count += r.delete(key)
        return count
