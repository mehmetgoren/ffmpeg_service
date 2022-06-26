import os

from common.utilities import logger
from rtmp.docker_manager import DockerManager
from stream.stream_model import StreamModel
from stream.stream_repository import StreamRepository
from stream.base_stream_event_handler import BaseStreamEventHandler
from utils.json_serializer import serialize_json


class StopStreamEventHandler(BaseStreamEventHandler):
    def __init__(self, stream_repository: StreamRepository):
        super().__init__(stream_repository, 'stop_stream_response')
        logger.info('StopStreamEventHandler initialized')

    def handle(self, dic: dict):  # which means operation is being stopped by a ruler, not by FFmpeg service itself.
        logger.info('StopStreamEventHandler handle called')
        # dic is request model with id
        is_valid_msg, sm, source_model = self.parse_message(dic)
        if not is_valid_msg:
            return
        stream_model: StreamModel = sm
        if stream_model is not None:
            try:
                self.stream_repository.remove(stream_model.id)  # remove it to prevent the process checker give it a life again.
            except BaseException as e:
                logger.error(f'Error while removing stream {stream_model.id} from repository: {e}')

            if stream_model.is_ffmpeg_snapshot_enabled():
                try:
                    if stream_model.snapshot_pid > 0:
                        os.kill(stream_model.snapshot_pid, 9)
                        logger.info(f'a FFMpeg Snapshot process has been killed, pid: {stream_model.snapshot_pid}')
                except BaseException as e:
                    logger.error(f'Error while killing a FFmpeg Snapshot stream process, pid: {stream_model.snapshot_pid}, err: {e}')

            if stream_model.is_record_enabled():
                try:
                    if stream_model.record_pid > 0:
                        os.kill(stream_model.record_pid, 9)
                        logger.info(f'a FFMpeg Recording process has been killed, pid: {stream_model.record_pid}')
                except BaseException as e:
                    logger.error(f'Error while killing a FFmpeg Recording process, pid: {stream_model.record_pid}, err: {e}')

            if stream_model.is_hls_enabled():
                try:
                    self.delete_prev_stream_files(stream_model.id)
                except BaseException as e:
                    logger.error(f'Error while deleting stream files for {stream_model.id}, err: {e}')
                try:
                    if stream_model.hls_pid > 0:
                        os.kill(stream_model.hls_pid, 9)
                        logger.info(f'a FFMpeg HLS process has been killed, pid: {stream_model.hls_pid}')
                except BaseException as e:
                    logger.error(f'Error while killing a FFmpeg HLS stream process, pid: {stream_model.hls_pid}, err: {e}')
            elif stream_model.is_ffmpeg_reader_enabled():
                try:
                    if stream_model.ffmpeg_reader_pid > 0:
                        os.kill(stream_model.ffmpeg_reader_pid, 9)
                        logger.info(f'a FFMpeg FFmpeg Reader process has been killed, pid: {stream_model.ffmpeg_reader_pid}')
                except BaseException as e:
                    logger.error(f'Error while killing a FFmpeg Reader process, pid: {stream_model.ffmpeg_reader_pid}, err: {e}')

            try:
                if stream_model.rtmp_feeder_pid > 0:
                    os.kill(stream_model.rtmp_feeder_pid, 9)
                    logger.info(f'a FFMpeg RTMP feeder process has been killed, pid: {stream_model.rtmp_feeder_pid}')
            except BaseException as e:
                logger.error(f'Error while killing process, pid: {stream_model.rtmp_feeder_pid}, err: {e}')

            try:
                docker_manager = DockerManager(self.stream_repository.connection)
                docker_manager.remove(stream_model)
                logger.info(f'a FFMpeg RTMP feeder container has been stopped and removed, pid: {stream_model.rtmp_feeder_pid}')
            except BaseException as e:
                logger.error(f'Error while removing RTMP container for {stream_model.id}, err: {e}')

        source_json = serialize_json(source_model)
        self.event_bus.publish_async(source_json)
