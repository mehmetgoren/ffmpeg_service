import os

from data.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler


class StopStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'stop_streaming_response')

    def handle(self, dic: dict):
        is_valid_msg, prev, model, json_str = self.parse_message(dic)
        if not is_valid_msg:
            return
        if prev is not None:
            self.streaming_repository.remove(prev.id)
            os.kill(prev.pid, 9)
        self.event_bus.publish(json_str)
