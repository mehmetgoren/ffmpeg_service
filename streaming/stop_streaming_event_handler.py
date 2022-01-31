import os

from common.utilities import logger
from streaming.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler


class StopStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'stop_streaming_response')
        logger.info('StopStreamingEventHandler initialized')

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        logger.info('StopStreamingEventHandler handle called')
        is_valid_msg, streaming_model, request_model, dic_json = self.parse_message(dic)  # dic is request model with id.
        if not is_valid_msg:
            return
        if streaming_model is not None:
            try:
                self.streaming_repository.remove(streaming_model.id)
            except BaseException as e:
                logger.error(f'Error while removing streaming {streaming_model.id} from repository: {e}')
            try:
                os.kill(streaming_model.pid, 9)
            except BaseException as e:
                logger.error(f'Error while killing process {streaming_model.pid}, err: {e}')
            try:
                self.delete_pref_streaming_files(streaming_model.id)
            except BaseException as e:
                logger.error(f'Error while deleting streaming files for {streaming_model.id}, err: {e}')
            # todo: remove container it its stream type is FLV.
        self.event_bus.publish(dic_json)
