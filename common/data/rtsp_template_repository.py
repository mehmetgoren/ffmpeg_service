from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository
from common.data.models import RtspTemplate


class RtspTemplateRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'rtsp_template:')

    def _get_key(self, identifier: str) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: RtspTemplate):
        key = self._get_key(model.id)
        dic = model.__dict__
        self.connection.hset(key, mapping=dic)

    def get(self, identifier: str) -> RtspTemplate:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        model = RtspTemplate()
        model.__dict__.update(dic)
        return model

    def get_all(self) -> List[RtspTemplate]:
        models: List[RtspTemplate] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = RtspTemplate()
            model.__dict__.update(dic)
            models.append(model)
        return models
