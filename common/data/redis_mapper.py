import enum
import json
from enum import IntEnum
from typing import Any

from common.utilities import logger


class DataTypes(IntEnum):
    STR = 0
    BOOL = 1
    INT = 2
    INT_ENUM = 3


class RedisMapper:
    def __init__(self, model: Any):
        self.type_name = type(model).__name__
        RedisMapper.__init_model_type(model, self.type_name)
        self.model = model
        self.encoding = 'utf-8'

    @staticmethod
    def is_pubsub_message_invalid(redis_binary_dic: dict):
        return redis_binary_dic is None or redis_binary_dic['type'] != 'message'

    # needs to mutate the model, using copy redundant here
    def from_redis_pubsub(self, redis_binary_dic: dict):
        data = redis_binary_dic['data']
        redis_dic = json.loads(data)
        field_types = self.__get_field_types()
        model_dic = self.model.__dict__
        for key, value in redis_dic.items():
            RedisMapper.__set_value(field_types, key, value, model_dic)
        return self.model

    # needs to mutate the model, using copy redundant here
    def from_redis(self, redis_binary_dic: dict) -> Any:
        field_types = self.__get_field_types()
        model_dic = self.model.__dict__
        for k, v in redis_binary_dic.items():
            key, value = k.decode(self.encoding), v.decode(self.encoding)
            RedisMapper.__set_value(field_types, key, value, model_dic)
        return self.model

    # do not mutate the model dictionary. Otherwise, it can cause big troubles
    def to_redis(self) -> dict:
        field_types = self.__get_field_types()
        model_dic = self.model.__dict__.copy()
        for key, value in self.model.__dict__.items():
            data_type = field_types[key]
            if data_type == DataTypes.BOOL:
                model_dic[key] = 1 if value else 0
            elif data_type == DataTypes.INT_ENUM:
                model_dic[key] = int(value)
            else:
                model_dic[key] = value
        return model_dic

    __cache = {}

    def __get_field_types(self):
        return RedisMapper.__cache[self.type_name]

    @staticmethod
    def __init_model_type(model, type_name: str):
        if type_name in RedisMapper.__cache:
            return
        model_dic = model.__dict__
        typed_dic = {}
        for model_field in model_dic:
            default_value = model_dic[model_field]
            # string is the most used type. No need to check if it is int or bool unnecessarily since it hurts performance
            if isinstance(default_value, str):
                typed_dic[model_field] = DataTypes.STR
            # bool value is also considered int, so it must be checked before int
            elif isinstance(default_value, bool):
                typed_dic[model_field] = DataTypes.BOOL
            elif isinstance(default_value, enum.IntEnum):
                typed_dic[model_field] = DataTypes.INT_ENUM
            elif isinstance(default_value, int):
                typed_dic[model_field] = DataTypes.INT
            else:
                raise NotImplementedError(type(default_value))
        RedisMapper.__cache[type_name] = typed_dic
        logger.warning(f'new type ({type_name}) added to RedisMapper cache')

    @staticmethod
    def __set_value(field_types: dict, key: str, value: str, dest_dict: dict):
        fns = RedisMapper.__get_init_cache_fns()
        data_type = field_types[key]
        dest_dict[key] = fns[data_type](value)

    __cache_fns = {}

    @staticmethod
    def __get_init_cache_fns():
        fns = RedisMapper.__cache_fns
        if len(fns) > 0:
            return fns

        def fn_str(value) -> str:
            return value

        def fn_bool(value) -> bool:
            return int(value) == 1

        def fn_int_enum(value) -> int:
            return int(value)

        def fn_int(value) -> int:
            return int(value)

        fns[DataTypes.STR] = fn_str
        fns[DataTypes.BOOL] = fn_bool
        fns[DataTypes.INT_ENUM] = fn_int_enum
        fns[DataTypes.INT] = fn_int
        logger.warning(f'new cached functions dictionary has been initialized')
        return fns
