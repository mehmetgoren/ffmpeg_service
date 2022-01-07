from typing import List
from redis import Redis

from common.data.models import ServiceModel


class ServiceRepository:
    def __init__(self, connection: Redis):
        self.connection: Redis = connection
        self.namespace = 'services:'

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
            fixed_dic = {k.decode('utf-8'): v.decode('utf-8') for k, v in dic.items()}
            model = ServiceModel(str(key).split(':')[1])
            model.__dict__.update(fixed_dic)
            models.append(model)
        return models
