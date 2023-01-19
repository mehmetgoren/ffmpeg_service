from __future__ import annotations

from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository
from common.data.rtsp_template_model import RtspTemplateModel


class RtspTemplateRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'rtsp_template:')

    def _get_key(self, identifier: str) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: RtspTemplateModel):
        key = self._get_key(model.id)
        dic = self.to_redis(model)
        self.connection.hset(key, mapping=dic)

    def get(self, identifier: str) -> RtspTemplateModel | None:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        return self.from_redis(RtspTemplateModel(), dic)

    def get_all(self) -> List[RtspTemplateModel]:
        models: List[RtspTemplateModel] = []
        keys = self.connection.keys(self.namespace + '*')
        for key in keys:
            dic = self.connection.hgetall(key)
            model: RtspTemplateModel = self.from_redis(RtspTemplateModel(), dic)
            models.append(model)
        return models
