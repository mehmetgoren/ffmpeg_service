import os

from common.data.source_model import StreamType
from common.utilities import logger
from rtmp.docker_manager import DockerManager
from streaming.streaming_repository import StreamingRepository
from streaming.base_streaming_event_handler import BaseStreamingEventHandler


class StopStreamingEventHandler(BaseStreamingEventHandler):
    def __init__(self, streaming_repository: StreamingRepository):
        super().__init__(streaming_repository, 'stop_streaming_response')
        logger.info('StopStreamingEventHandler initialized')

    # todo: the whole process needs to be handled by rq-redis
    def handle(self, dic: dict):
        logger.info('StopStreamingEventHandler handle called')
        # dic is request model with id
        is_valid_msg, streaming_model, request_model, dic_json = self.parse_message(dic)
        if not is_valid_msg:
            return
        if streaming_model is not None:
            try:
                self.streaming_repository.remove(streaming_model.id)
            except BaseException as e:
                logger.error(f'Error while removing streaming {streaming_model.id} from repository: {e}')

            try:
                os.kill(streaming_model.pid, 9)  # pid kill also stop FFmpeg direct read process too.
            except BaseException as e:
                logger.error(f'Error while killing process {streaming_model.pid}, err: {e}')

            if streaming_model.streaming_type == StreamType.HLS:
                try:
                    self.delete_pref_streaming_files(streaming_model.id)
                except BaseException as e:
                    logger.error(f'Error while deleting streaming files for {streaming_model.id}, err: {e}')

            if streaming_model.streaming_type == StreamType.FLV:
                try:
                    docker_manager = DockerManager(self.streaming_repository.connection)
                    docker_manager.remove(streaming_model)
                except BaseException as e:
                    logger.error(f'Error while removing FLC container for {streaming_model.id}, err: {e}')

        self.event_bus.publish(dic_json)
