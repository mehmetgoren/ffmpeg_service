import os

from common.data.source_model import StreamType
from common.utilities import logger
from rtmp.docker_manager import DockerManager
from stream.stream_repository import StreamRepository
from stream.base_stream_event_handler import BaseStreamEventHandler


class StopStreamEventHandler(BaseStreamEventHandler):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository, 'stop_stream_response')
        logger.info('StopStreamEventHandler initialized')

    def handle(self, dic: dict):
        logger.info('StopStreamEventHandler handle called')
        # dic is request model with id
        is_valid_msg, stream_model, request_model, dic_json = self.parse_message(dic)
        if not is_valid_msg:
            return
        if stream_model is not None:
            try:
                self.stream_repository.remove(stream_model.id)
            except BaseException as e:
                logger.error(f'Error while removing stream {stream_model.id} from repository: {e}')

            try:
                os.kill(stream_model.pid, 9)  # pid kill also stop FFmpeg direct read process too.
            except BaseException as e:
                logger.error(f'Error while killing process {stream_model.pid}, err: {e}')

            if stream_model.stream_type == StreamType.HLS:
                try:
                    self.delete_prev_stream_files(stream_model.id)
                except BaseException as e:
                    logger.error(f'Error while deleting stream files for {stream_model.id}, err: {e}')

            if stream_model.stream_type == StreamType.FLV:
                if stream_model.record:
                    try:
                        os.kill(stream_model.record_flv_pid, 9)
                    except BaseException as e:
                        logger.error(f'Error while killing record FFmpeg process for {stream_model.id}, err: {e}')

                try:
                    docker_manager = DockerManager(self.stream_repository.connection)
                    docker_manager.remove(stream_model)
                except BaseException as e:
                    logger.error(f'Error while removing FLV container for {stream_model.id}, err: {e}')

        self.event_bus.publish(dic_json)
