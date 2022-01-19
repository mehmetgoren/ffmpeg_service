# this section will move to the common package and ml_services will reorganize again.
from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository


class Source:
    def __init__(self, identifier: str = '', name: str = '', rtsp_address: str = ''):
        self.id = identifier
        self.name = name
        self.rtsp_address = rtsp_address
        self.brand = 'Generic'


class SourceRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'sources:')

    def _get_key(self, identifier: str) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: Source):
        key = self._get_key(model.id)
        dic = model.__dict__
        self.connection.hset(key, mapping=dic)

    def get(self, identifier: str) -> Source:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        model = Source()
        # todo: replace it model.__dict__.update(dic) when 'pickle_data' and 'json_data' are removed
        model.id = dic['id']
        model.name = dic['name']
        model.rtsp_address = dic['rtsp_address']
        model.brand = dic['brand']
        return model

    def get_all(self) -> List[Source]:
        models: List[Source] = []
        keys = self.connection.keys()
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = Source()
            # todo: replace it model.__dict__.update(dic) when 'pickle_data' and 'json_data' are removed
            model.id = dic['id']
            model.name = dic['name']
            model.rtsp_address = dic['rtsp_address']
            model.brand = dic['brand']
            models.append(model)
        return models
