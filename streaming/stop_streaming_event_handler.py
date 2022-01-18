import os

from common.utilities import logger
from data.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler
from streaming.hls_streaming import _delete_pref_streaming_files


class StopStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'stop_streaming_response')

    def handle(self, dic: dict):
        is_valid_msg, prev, model, json_str = self.parse_message(dic)
        if not is_valid_msg:
            return
        if prev is not None:
            try:
                self.streaming_repository.remove(prev.id)
            except BaseException as e:
                logger.error(f'Error while removing streaming {prev.id} from repository: {e}')
            try:
                os.kill(prev.pid, 9)
            except BaseException as e:
                logger.error(f'Error while killing process {prev.pid}')
            try:
                _delete_pref_streaming_files(prev)
            except BaseException as e:
                logger.error(f'Error while deleting streaming files for {prev.id}')
        self.event_bus.publish(json_str)
