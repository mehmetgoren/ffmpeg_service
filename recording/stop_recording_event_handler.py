import os

from data.recording_repository import RecordingRepository
from recording.base_recording_event_handler import BaseRecordingEventHandler


class StopRecordingEventHandler(BaseRecordingEventHandler):
    def __init__(self, recording_repository: RecordingRepository):
        super().__init__(recording_repository, 'stop_recording_response')

    def handle(self, dic: dict):
        is_valid_msg, prev, model, json_str = self.check_message(dic)
        if not is_valid_msg:
            return
        if prev is not None:
            self.recording_repository.remove(prev.id)
            os.kill(prev.pid, 9)
        self.event_bus.publish(json_str)
