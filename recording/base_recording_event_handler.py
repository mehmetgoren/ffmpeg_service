import json
from abc import ABC

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from data.models import RecordingModel
from data.recording_repository import RecordingRepository


class BaseRecordingEventHandler(EventHandler, ABC):
    def __init__(self, recording_repository: RecordingRepository, response_channel_name: str):
        self.encoding = 'utf-8'
        self.event_bus = EventBus(response_channel_name)
        self.recording_repository = recording_repository

    def check_message(self, dic: dict) -> (bool, RecordingModel, RecordingModel, str):
        if dic is None or dic['type'] != 'message':
            return False, None, None, ''

        data: bytes = dic['data']
        json_str = data.decode(self.encoding)
        fixed_dic = json.loads(json_str)
        model = RecordingModel().map_from(fixed_dic)
        prev = self.recording_repository.get(model.id)

        return True, prev, model, json_str
