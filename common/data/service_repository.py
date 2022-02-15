from typing import List
from redis import Redis

from common.data.base_repository import BaseRepository
from common.data.service_model import ServiceModel


class ServiceRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'services:')

    def _get_key(self, service_name: str) -> str:
        return f'{self.namespace}{service_name}'

    def add(self, service_name: str, description: str = ''):
        key = self._get_key(service_name)
        model = ServiceModel(service_name)
        model.description = description
        model.detect_values()
        dic = self.to_redis(model)
        self.connection.hset(key, mapping=dic)

    def get_all(self) -> List[ServiceModel]:
        models: List[ServiceModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            model: ServiceModel = self.from_redis(ServiceModel(str(key).split(':')[1]), dic)
            models.append(model)
        return models
