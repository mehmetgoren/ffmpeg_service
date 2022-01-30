import json

from redis import Redis


def is_message_invalid(dic: dict):
    return dic is None or dic['type'] != 'message'


def fix_redis_pubsub_dict(redis_dic: dict, encoding: str) -> (dict, str):
    data: bytes = redis_dic['data']
    json_str = data.decode(encoding)
    fixed_dic = json.loads(json_str)
    return fixed_dic, json_str


def fix_dic_fields_bool_to_int(dic: dict) -> dict:
    for field in dic:
        value = dic[field]
        if isinstance(value, bool):
            dic[field] = 1 if value else 0
    return dic


def map_from(source: dict, default_dest, dest):
    default_dic = default_dest.__dict__
    typed_dic = {}
    for field in default_dic:
        if field not in source:
            continue
        default_value = default_dic[field]
        # string is the most used type. No need to check if it is int or bool unnecessarily since it hurts performance
        if isinstance(default_value, str):
            typed_dic[field] = source[field]
        # bool value is also considered int, so it must be checked before int
        elif isinstance(default_value, bool):
            typed_dic[field] = int(source[field]) == 1
        elif isinstance(default_value, int):
            typed_dic[field] = int(source[field])
        else:
            raise NotImplementedError(type(default_value))
    dest.__dict__.update(typed_dic)
    return dest


class BaseRepository:
    def __init__(self, connection: Redis, namespace: str):
        self.connection: Redis = connection
        self.namespace: str = namespace
        self._encoding = 'utf-8'

    def fix_bin_redis_dic(self, dic: dict) -> dict:
        return {k.decode(self._encoding): v.decode(self._encoding) for k, v in dic.items()}
