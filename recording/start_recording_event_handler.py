import time
from threading import Thread

from data.models import RecordingModel
from data.recording_repository import RecordingRepository
from recording.base_recording_event_handler import BaseRecordingEventHandler
from recording.mp4_recording import start_recording


class StartRecordingEventHandler(BaseRecordingEventHandler):
    def __init__(self, recording_repository: RecordingRepository):
        super().__init__(recording_repository, 'start_recording_response')

    def handle(self, dic: dict):
        is_valid_msg, prev, model, json_str = self.parse_message(dic)
        if not is_valid_msg:
            return
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
