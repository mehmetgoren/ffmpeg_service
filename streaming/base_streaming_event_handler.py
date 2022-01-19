from abc import ABC

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from data.models import StreamingModel
from data.streaming_repository import StreamingRepository
from utils.redis import is_message_invalid, fix_redis_pubsub_dict


class BaseStreamingEventHandler(EventHandler, ABC):
    def __init__(self, streaming_repository: StreamingRepository, response_channel_name: str):
        self.encoding = 'utf-8'
        self.event_bus = EventBus(response_channel_name)
        self.streaming_repository = streaming_repository

    def parse_message(self, dic: dict) -> (bool, StreamingModel, StreamingModel, str):
        if is_message_invalid(dic):
            return False, None, None, ''

        fixed_dic, json_str = fix_redis_pubsub_dict(dic, self.encoding)
        model = StreamingModel().map_from(fixed_dic)
        prev = self.streaming_repository.get(model.id)

        return True, prev, model, json_str
