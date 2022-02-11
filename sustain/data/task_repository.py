from typing import List
from redis.client import Redis

from common.data.base_repository import BaseRepository, fix_dic_fields_bool_to_int, fix_dic_field_enum_to_int
from sustain.data.task import Task, TaskOp


class TaskRepository(BaseRepository):
    def __init__(self, connection: Redis):
        super().__init__(connection, 'tasks:')

    def _get_key(self, identifier: TaskOp) -> str:
        return f'{self.namespace}{identifier}'

    def add(self, model: Task):
        key = self._get_key(model.op)
        dic = model.__dict__
        fix_dic_fields_bool_to_int(dic)
        fix_dic_field_enum_to_int(dic, ['op'])
        self.connection.hset(key, mapping=dic)

    def remove_all(self) -> int:
        r = self.connection
        count = 0
        for key in r.scan_iter(f'{self.namespace}*'):
            count += r.delete(key)
        return count

    def get_all(self) -> List[Task]:
        models: List[Task] = []
        keys = self.connection.keys(f'{self.namespace}*')
        for key in keys:
            dic = self.connection.hgetall(key)
            dic = self.fix_bin_redis_dic(dic)
            model = Task().map_from(dic)
            models.append(model)
        return models

    def get(self, identifier: TaskOp) -> Task:
        key = self._get_key(identifier)
        dic = self.connection.hgetall(key)
        if not dic:
            return None
        dic = self.fix_bin_redis_dic(dic)
        return Task().map_from(dic)
