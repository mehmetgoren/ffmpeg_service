import asyncio
import json
import time
from threading import Thread

from common.event_bus.event_bus import EventBus
from common.event_bus.event_handler import EventHandler
from data.models import RecordingModel
from data.recording_repository import RecordingRepository
from recording.mp4_recording import start_recording


class StartRecordingEventHandler(EventHandler):
    def __init__(self, recording_repository: RecordingRepository):
        self.encoding = 'utf-8'
        self.event_bus = EventBus('start_recording_response')
        self.recording_repository = recording_repository

    def handle(self, dic: dict):
        if dic is None or dic['type'] != 'message':
            return

        data: bytes = dic['data']
        json_str = data.decode(self.encoding)
        fixed_dic = json.loads(json_str)
        model = RecordingModel().map_from(fixed_dic)
        prev = self.recording_repository.get(model.id)

        if prev is None:
            self.start_recording(model)

        self.event_bus.publish(json_str)

    def start_recording(self, model: RecordingModel):
        th = Thread(target=self.__handle, args=[model])
        th.daemon = True
        th.start()
        # todo: move to ml-config
        time.sleep(10)

    def __handle(self, model: RecordingModel):
        start_recording(self.recording_repository.get_connection(), model)
