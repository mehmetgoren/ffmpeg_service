import json


def is_message_invalid(dic: dict):
    return dic is None or dic['type'] != 'message'


def fix_redis_pubsub_dict(redis_dic: dict, encoding: str) -> (dict, str):
    data: bytes = redis_dic['data']
    json_str = data.decode(encoding)
    fixed_dic = json.loads(json_str)
    return fixed_dic, json_str
