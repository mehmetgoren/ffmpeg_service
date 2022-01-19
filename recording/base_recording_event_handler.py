from abc import ABC

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from data.models import RecordingModel
from data.recording_repository import RecordingRepository
from utils.redis import is_message_invalid, fix_redis_pubsub_dict


class BaseRecordingEventHandler(EventHandler, ABC):
    def __init__(self, recording_repository: RecordingRepository, response_channel_name: str):
        self.encoding = 'utf-8'
        self.event_bus = EventBus(response_channel_name)
        self.recording_repository = recording_repository

    def parse_message(self, dic: dict) -> (bool, RecordingModel, RecordingModel, str):
        if is_message_invalid(dic):
            return False, None, None, ''

        fixed_dic, json_str = fix_redis_pubsub_dict(dic, self.encoding)
        model = RecordingModel().map_from(fixed_dic)
        prev = self.recording_repository.get(model.id)

        return True, prev, model, json_str
