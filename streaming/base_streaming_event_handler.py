import json
from abc import ABC

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from data.models import StreamingModel
from data.streaming_repository import StreamingRepository


class BaseStreamingEventHandler(EventHandler, ABC):
    def __init__(self, streaming_repository: StreamingRepository, response_channel_name: str):
        self.encoding = 'utf-8'
        self.event_bus = EventBus(response_channel_name)
        self.streaming_repository = streaming_repository

    def parse_message(self, dic: dict) -> (bool, StreamingModel, StreamingModel, str):
        if dic is None or dic['type'] != 'message':
            return False, None, None, ''

        data: bytes = dic['data']
        json_str = data.decode(self.encoding)
        fixed_dic = json.loads(json_str)
        model = StreamingModel().map_from(fixed_dic)
        prev = self.streaming_repository.get(model.id)

        return True, prev, model, json_str
