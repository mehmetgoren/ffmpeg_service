import json
from types import SimpleNamespace


def serialize_json(obj):
    dic = {}
    dic.update(obj.__dict__)
    return json.dumps(dic, default=lambda o: o.__dict__,
                      sort_keys=True, indent=4)


def serialize_json_dic(dic: dict) -> str:
    return json.dumps(dic, ensure_ascii=False, indent=4)


def deserialize_json(json_str, result):
    simple_namespace = json.loads(json_str, object_hook=lambda d: SimpleNamespace(**d))
    result.__dict__.update(simple_namespace.__dict__)
    return result
