from __future__ import annotations

from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository
from sustain.task.task_model import TaskModel, TaskOp


class TaskRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'tasks:')

    def _get_key(self, identifier: TaskOp) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: TaskModel):
        key = self._get_key(model.op)
        dic = self.to_redis(model)
        self.connection.hset(key, mapping=dic)

    def remove_all(self) -> int:
        r = self.connection
        count = 0
        for key in r.scan_iter(f'{self.namespace}*'):
            count += r.delete(key)
        return count

    def get_all(self) -> List[TaskModel]:
        models: List[TaskModel] = []
        keys = self.connection.keys(f'{self.namespace}*')
        for key in keys:
            dic = self.connection.hgetall(key)
            model: TaskModel = self.from_redis(TaskModel(), dic)
            models.append(model)
        return models

    def get(self, identifier: TaskOp) -> TaskModel | None:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        return self.from_redis(TaskModel(), dic)
