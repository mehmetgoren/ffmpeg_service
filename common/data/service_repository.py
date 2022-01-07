from typing import List
from redis import Redis

from common.data.base_repository import BaseRepository
from common.data.models import ServiceModel


class ServiceRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'services:')

    def _get_key(self, service_name: str) -> str:
        return f'{self.namespace}{service_name}'

    def add(self, service_name: str):
        key = self._get_key(service_name)
        model = ServiceModel(service_name)
        model.detect_values()
        self.connection.hset(key, mapping=model.__dict__)

    def get_all(self) -> List[ServiceModel]:
        models: List[ServiceModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            fixed_dic = self.fix_bin_redis_dic(dic)
            model = ServiceModel(str(key).split(':')[1])
            model.__dict__.update(fixed_dic)
            models.append(model)
        return models
