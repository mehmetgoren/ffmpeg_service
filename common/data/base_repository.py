from redis import Redis


class BaseRepository:
    def __init__(self, connection: Redis, namespace: str):
        self.connection: Redis = connection
        self.namespace: str = namespace
        self._encoding = 'utf-8'

    def fix_bin_redis_dic(self, dic: dict) -> dict:
        return {k.decode(self._encoding): v.decode(self._encoding) for k, v in dic.items()}
